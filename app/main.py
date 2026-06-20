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

import nest_asyncio
nest_asyncio.apply()

import asyncio
import queue
import threading
import time

import streamlit as st
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import get_workflow


def run_workflow_in_thread(
    user_query: str,
    session_id: str,
    session_service: InMemorySessionService,
    q: queue.Queue,
) -> None:
    """Creates a new event loop and runs the ADK workflow, sending events back via a queue."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _run() -> None:
        try:
            try:
                await session_service.create_session(
                    app_name="app", user_id="user", session_id=session_id
                )
            except Exception:
                pass

            message = types.Content(role="user", parts=[types.Part.from_text(text=user_query)])

            # Create workflow and runner fresh on the thread's event loop!
            workflow = get_workflow()
            runner = Runner(
                agent=workflow,
                app_name="app",
                session_service=session_service,
            )

            async for event in runner.run_async(
                user_id="user",
                session_id=session_id,
                new_message=message,
            ):
                q.put(("event", event))

            session = await session_service.get_session(
                app_name="app", user_id="user", session_id=session_id
            )
            skill_matrix = session.state.get("skill_matrix")
            interview_prep = session.state.get("interview_prep")
            q.put(("done", (skill_matrix, interview_prep)))
        except Exception as e:
            q.put(("error", e))
        finally:
            q.put(("sentinel", None))

    loop.run_until_complete(_run())
    loop.close()


def run_chat_turn(user_query: str) -> None:
    """Executes a single workflow turn in a background thread and streams replies to the UI."""
    q = queue.Queue()

    t = threading.Thread(
        target=run_workflow_in_thread,
        args=(
            user_query,
            st.session_state.session_id,
            st.session_state.session_service,
            q,
        ),
        daemon=True,
    )
    t.start()

    full_reply = ""
    message_placeholder = st.empty()

    while True:
        try:
            item = q.get(timeout=0.1)
        except queue.Empty:
            continue

        msg_type, data = item
        if msg_type == "sentinel":
            break
        elif msg_type == "error":
            raise data
        elif msg_type == "event":
            event = data
            if event.author == "ChatResponder":
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            full_reply += part.text
                            message_placeholder.markdown(full_reply)
        elif msg_type == "done":
            skill_matrix, interview_prep = data
            st.session_state.skill_matrix = skill_matrix
            st.session_state.interview_prep = interview_prep


def main() -> None:
    st.set_page_config(layout="wide", page_title="VibeJournal SE Mentor")

    # Initialize persistent state variables across Streamlit runs
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session_{int(time.time())}"
    if "session_service" not in st.session_state:
        st.session_state.session_service = InMemorySessionService()
    # Runner is created dynamically per chat-turn inside the background thread
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "skill_matrix" not in st.session_state:
        st.session_state.skill_matrix = None
    if "interview_prep" not in st.session_state:
        st.session_state.interview_prep = None

    st.title("🎓 VibeJournal - AI & Software Engineering Mentor")
    st.write(
        "Welcome! Speak with your encouraging mentor below to assess your skills and get personalized mock interview preps."
    )

    # Create the dual-panel layout
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("💬 Conversation with Mentor")

        # Container for chat history
        chat_container = st.container(height=500)
        with chat_container:
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["text"])

        # Capture user input
        if prompt := st.chat_input("Message your mentor..."):
            # Display user message immediately
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    # Run the turn via background thread and stream response
                    run_chat_turn(prompt)
            # Rerun streamlit to update the state display on the right panel
            st.rerun()

    with col_right:
        st.subheader("📊 Skill Profile & Analytics")

        matrix = st.session_state.skill_matrix
        if matrix:
            # Display scores as progress bars
            st.write("**AI Foundations Score:**")
            st.progress(int(matrix.get("ai_foundations_score", 0)) / 100.0)
            st.caption(f"{matrix.get('ai_foundations_score', 0)} / 100")

            st.write("**Agentic AI Score:**")
            st.progress(int(matrix.get("agentic_ai_score", 0)) / 100.0)
            st.caption(f"{matrix.get('agentic_ai_score', 0)} / 100")

            st.write("**System Design Score:**")
            st.progress(int(matrix.get("system_design_score", 0)) / 100.0)
            st.caption(f"{matrix.get('system_design_score', 0)} / 100")

            # Weaknesses & takeaways
            st.info(f"**Primary Weak Area:**\n{matrix.get('primary_weak_area', 'N/A')}")
            st.success(
                f"**Improving Trends:**\n{matrix.get('improving_trends', 'N/A')}"
            )
            st.warning(
                f"**Key Takeaway Logged:**\n{matrix.get('key_takeaway_logged', 'N/A')}"
            )
        else:
            st.info(
                "No evaluation metrics generated yet. Start chatting to assess your skills!"
            )

        st.subheader("📝 Tailored Mock Interview Prep")
        prep = st.session_state.interview_prep
        if prep:
            st.write(
                f"**Mock Interview Question:**\n{prep.get('mock_interview_question', 'N/A')}"
            )

            # Hidden grading rubrics in expander
            with st.expander("🔍 View Hidden Grading Rubric"):
                rubrics = prep.get("hidden_grading_rubric") or []
                for idx, rubric in enumerate(rubrics, 1):
                    st.write(f"{idx}. {rubric}")

            st.write("**Ideal Architectural Answer:**")
            st.code(prep.get("ideal_architectural_answer", "N/A"), language="text")
        else:
            st.info("Assessment mock interview prep will display here.")


if __name__ == "__main__":
    main()
