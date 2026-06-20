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

from pydantic import BaseModel, Field


class SkillMatrix(BaseModel):
    """Pydantic model representing score matrices and takeaways for skills evaluation."""

    ai_foundations_score: int = Field(
        ..., ge=1, le=100, description="AI Foundations score scaled 1-100"
    )
    agentic_ai_score: int = Field(
        ..., ge=1, le=100, description="Agentic AI score scaled 1-100"
    )
    system_design_score: int = Field(
        ..., ge=1, le=100, description="System Design score scaled 1-100"
    )
    primary_weak_area: str = Field(
        ..., description="Identified primary weak area to focus on"
    )
    improving_trends: str = Field(
        ..., description="Description of improving performance trends"
    )
    key_takeaway_logged: str = Field(
        ..., description="Core takeaways logged during the evaluation"
    )


class InterviewPrep(BaseModel):
    """Pydantic model representing mock interview prep questions, rubrics, and answers."""

    mock_interview_question: str = Field(
        ..., description="The mock interview question presented to the candidate"
    )
    hidden_grading_rubric: list[str] = Field(
        ..., description="A list containing 3-4 structural criteria used for grading"
    )
    ideal_architectural_answer: str = Field(
        ..., description="Text block representing the ideal architectural answer"
    )
