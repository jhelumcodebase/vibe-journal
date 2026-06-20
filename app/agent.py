# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import asyncio
import datetime
import logging
from zoneinfo import ZoneInfo

from google.adk.agents import LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.workflow import Workflow
from google.cloud import firestore
from google.genai import types
from pydantic import BaseModel

import os
import google.auth
from dotenv import load_dotenv
from .state_schema import SkillMatrix, InterviewPrep

load_dotenv()

logger = logging.getLogger(__name__)

_, project_id = google.auth.default()
project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
if project_id:
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


class WorkflowState(BaseModel):
    """Workflow state validation schema."""

    skill_matrix: SkillMatrix | None = None
    interview_prep: InterviewPrep | None = None


# Agents and workflow are created lazily in get_workflow() to avoid event loop conflicts.


async def _write_to_firestore_async(
    session_id: str,
    query: str,
    reply: str,
    skill_matrix: dict,
    interview_prep: dict,
    key_takeaway: str,
) -> None:
    """Safely and asynchronously writes the turn log to Google Cloud Firestore in the background."""
    try:
        db = firestore.AsyncClient()
        doc_data = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc),
            "user_query": query,
            "ai_reply": reply,
            "key_takeaway_logged": key_takeaway,
            "skill_matrix": skill_matrix,
            "interview_prep": interview_prep,
        }
        # Save directly under sessions/{session_id}/historical_logs/{auto_id}
        doc_ref = (
            db.collection("sessions")
            .document(session_id)
            .collection("historical_logs")
            .document()
        )
        await doc_ref.set(doc_data)
        logger.info(f"Successfully logged turn to Firestore for session {session_id}")
    except Exception as e:
        logger.exception(f"Failed to write to Firestore for session {session_id}: {e}")


class FirestoreLoggerPlugin(BasePlugin):
    """ADK plugin to asynchronously log session history and metrics to Firestore on run completion."""

    def __init__(self, name: str = "firestore_logger") -> None:
        super().__init__(name=name)

    async def after_run_callback(
        self, *, invocation_context: InvocationContext
    ) -> None:
        """Executes on workflow run completion, extracting and logging metrics asynchronously."""
        session = invocation_context.session
        session_id = session.id
        state = session.state
        skill_matrix = state.get("skill_matrix") or {}
        interview_prep = state.get("interview_prep") or {}
        key_takeaway = skill_matrix.get("key_takeaway_logged", "")

        # Retrieve user query and AI response from session events
        events = session.events
        query = ""
        for event in reversed(events):
            if event.author == "user":
                if event.content and event.content.parts:
                    query = "".join(
                        part.text for part in event.content.parts if part.text
                    )
                    break

        reply = ""
        for event in reversed(events):
            if event.author in ("ChatResponder", "vibe_journal_workflow", "app"):
                if event.content and event.content.parts:
                    reply = "".join(
                        part.text for part in event.content.parts if part.text
                    )
                    break

        if not reply:
            for event in reversed(events):
                if event.author != "user" and event.content and event.content.parts:
                    reply = "".join(
                        part.text for part in event.content.parts if part.text
                    )
                    break

        # Spawn firestore write asynchronously in background to ensure zero UI lag
        asyncio.create_task(
            _write_to_firestore_async(
                session_id=session_id,
                query=query,
                reply=reply,
                skill_matrix=skill_matrix,
                interview_prep=interview_prep,
                key_takeaway=key_takeaway,
            )
        )


def get_workflow() -> Workflow:
    """Returns a fresh workflow instance bound to the current event loop."""
    chat_responder = LlmAgent(
        name="ChatResponder",
        model=Gemini(
            model="gemini-2.5-flash",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction=(
            "Act as an encouraging AI/Software Engineering mentor. Provide immediate "
            "answers/guidance to incoming user prompts based on conversational history context."
        ),
    )

    skill_evaluator = LlmAgent(
        name="SkillEvaluator",
        model=Gemini(
            model="gemini-2.5-pro",
            retry_options=types.HttpRetryOptions(attempts=5),
        ),
        instruction=(
            "Analyze the full conversation history, audit the user's technical gaps "
            "and skills, and strictly populate the structured JSON data using the SkillMatrix model."
        ),
        output_schema=SkillMatrix,
        output_key="skill_matrix",
    )

    interview_coach = LlmAgent(
        name="InterviewCoach",
        model=Gemini(
            model="gemini-2.5-pro",
            retry_options=types.HttpRetryOptions(attempts=5),
        ),
        instruction=(
            "Read the evaluated weakness from 'skill_matrix' in the workflow state, "
            "and output a tailored mock interview simulation mapping directly to the "
            "InterviewPrep schema structure."
        ),
        output_schema=InterviewPrep,
        output_key="interview_prep",
    )

    return Workflow(
        name="vibe_journal_workflow",
        edges=[
            ("START", chat_responder),
            (chat_responder, skill_evaluator),
            (skill_evaluator, interview_coach),
        ],
        state_schema=WorkflowState,
    )


# Default module-level workflow for backward compatibility
app_workflow = get_workflow()

# Export app referencing our workflow as root_agent and registering our logger plugin
app = App(
    root_agent=app_workflow,
    name="app",
    plugins=[FirestoreLoggerPlugin()],
)
