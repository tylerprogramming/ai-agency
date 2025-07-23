from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from .tools.custom_tool import AddEventTool
from .tools.delete_event_tool import DeleteEventTool
from .tools.update_event_tool import UpdateEventTool
from .tools.select_events_tool import SelectEventsTool
from dotenv import load_dotenv
load_dotenv()

@CrewBase
class CalendarCrew():
    """CalendarCrew crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def intent_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['intent_agent'],
            verbose=True
        )

    @agent
    def calendar_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['calendar_agent'],
            verbose=True,
            tools=[AddEventTool(), DeleteEventTool(), UpdateEventTool(), SelectEventsTool()]
        )

    @task
    def intent_task(self) -> Task:
        return Task(
            config=self.tasks_config['intent_task'], # type: ignore[index]
        )

    @task
    def calendar_task(self) -> Task:
        return Task(
            config=self.tasks_config['calendar_task'], # type: ignore[index]
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CalendarCrew crew"""

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
