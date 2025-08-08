#!/usr/bin/env python3
"""
ContentService - runs a CrewAI agent/task/crew to generate content for a given document type
"""

from typing import Optional
from pydantic import BaseModel
from crewai import Agent, Task, Crew


class ContentOutput(BaseModel):
    task: str
    content: str


class ContentService:
    def run_content_agent(
        self,
        document_type_prompt: str,
        task: str,
        extra_context: Optional[str] = None,
        verbose: bool = True,
    ) -> ContentOutput:
        """Execute an Agent → Task → Crew pipeline to produce content.

        Args:
            document_type_prompt: A short prompt describing the document type (e.g., "Blog", "Webinar", "Instagram", "Email").
            task: The specific task to complete (e.g., "Write a blog about X"). This will be returned in the output.
            extra_context: Optional additional context to guide the agent (persona, tone, examples, etc.).
            verbose: Whether to run the agent and crew in verbose mode.

        Returns:
            ContentOutput: pydantic model with the original task and generated content.
        """

        # Build an agent focused on the specified document type
        content_agent = Agent(
            role="Content Creator",
            goal=f"Create high-quality {document_type_prompt} content for the specified task.",
            backstory=(
                "You are an experienced content creator. You produce concise, clear, and on-brand "
                f"deliverables tailored to the document type: {document_type_prompt}."
            ),
            verbose=verbose,
        )

        # Compose the task description
        description_lines = [
            f"Document Type: {document_type_prompt}",
            f"Task: {task}",
        ]
        if extra_context:
            description_lines.append(f"Context: {extra_context}")
        description = "\n".join(description_lines)

        # Define the CrewAI task – ensure output includes the task and content
        content_task = Task(
            description=description,
            expected_output=(
                "Return a structured output containing the fields 'task' (same as provided) "
                "and 'content' (the generated content for this task)."
            ),
            agent=content_agent,
            output_pydantic=ContentOutput,
        )

        # Run the crew
        crew = Crew(agents=[content_agent], tasks=[content_task], verbose=verbose)
        result = crew.kickoff()

        # Fill task if model omitted it for any reason
        output = result.pydantic
        if not getattr(output, "task", None):
            output.task = task
        return output


