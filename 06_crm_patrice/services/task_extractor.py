#!/usr/bin/env python3
"""
TaskExtractor - wrapper calling existing CrewAI logic in client_monitor without duplicating config
"""

from typing import List
from pydantic import BaseModel
from crewai import Agent, Task, Crew


class WeeklyTasks(BaseModel):
    tasks: List[str]


class TaskExtractor:
    def extract_weekly_tasks(self, transcript: str) -> WeeklyTasks:
        if not transcript:
            return WeeklyTasks(tasks=[])

        transcript_agent = Agent(
            role="Research Analyst",
            goal=f"Take the transcript and extract the weekly tasks: {transcript}",
            backstory="You are an experienced task extractor with attention to detail.",
            verbose=True,
        )

        task_extraction_task = Task(
            description=f"Extract weekly tasks from the transcript: {transcript}",
            expected_output="A list of weekly tasks",
            agent=transcript_agent,
            output_pydantic=WeeklyTasks,
        )

        crew = Crew(agents=[transcript_agent], tasks=[task_extraction_task], verbose=True)
        result = crew.kickoff()
        return result.pydantic

