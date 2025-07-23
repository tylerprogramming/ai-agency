import os
import json
from typing import List, Dict, Any
from datetime import datetime

from crewai import Agent, Task, Crew, Process
from ..models.schemas import ParsedEvent, EventParsingOutput
from ..calendar_crew.src.calendar_crew.main import run as calendar_crew_run
from ..calendar_crew.src.calendar_crew.tools.custom_tool import AddEventTool


class AIService:
    def __init__(self):
        self.add_event_tool = AddEventTool()

    def parse_text_to_events(self, text: str, openai_api_key: str) -> Dict[str, Any]:
        """Parse free-form text and create calendar events using CrewAI agents"""
        # Define the event parsing agent
        event_parser_agent = Agent(
            role="Calendar Event Parser Specialist",
            goal="Parse free-form text and extract structured calendar event information with high accuracy",
            backstory="""You are an expert at interpreting natural language descriptions of events and 
            converting them into structured calendar entries. You excel at understanding dates, times, 
            locations, and other event details from casual descriptions. You always use proper timezone 
            handling and make reasonable assumptions for missing information.""",
            verbose=True,
            llm=f"openai/gpt-4.1",
            max_iter=3,
            allow_code_execution=False
        )
        
        # Create the event creation task
        parsing_task = Task(
            description=f"""
            Parse the following text and extract calendar event information:
            
            TEXT TO PARSE: {text}
            
            Rules for parsing:
            1. If no year is mentioned, assume current year (2025)
            2. If no time is mentioned, assume 1-hour duration starting at a reasonable time (9 AM for meetings, appropriate times for meals, etc.)
            3. Use "America/New_York" timezone unless explicitly specified otherwise
            4. Extract location only if explicitly mentioned in the text
            5. Extract attendees only if email addresses are provided
            6. Make reasonable assumptions for missing information
            7. For relative dates like "tomorrow", "next week", calculate based on today being {datetime.now().strftime('%B %d, %Y')}
            8. If multiple events are mentioned, include all of them
            9. Be conservative - only create events that are clearly intended as calendar events
            
            Current date context: Today is {datetime.now().strftime('%A, %B %d, %Y')}
            """,
            expected_output="A structured JSON response containing the parsed events in the specified format",
            agent=event_parser_agent,
            output_pydantic=EventParsingOutput
        )
        
        # Create and run the crew
        crew = Crew(
            agents=[event_parser_agent],
            tasks=[parsing_task],
            process=Process.sequential,
            verbose=True
        )
        
        # Set the OpenAI API key for the crew
        original_key = os.environ.get('OPENAI_API_KEY')
        os.environ['OPENAI_API_KEY'] = openai_api_key
        
        try:
            # Execute the crew
            result = crew.kickoff()
            
            # Parse the result
            if hasattr(result, 'pydantic') and result.pydantic:
                parsed_output = result.pydantic
                events_data = [event.dict() for event in parsed_output.events]
            else:
                # Fallback parsing if pydantic output is not available
                result_text = str(result)
                try:
                    # Try to extract JSON from the result
                    if '{' in result_text and '}' in result_text:
                        start_idx = result_text.find('{')
                        end_idx = result_text.rfind('}') + 1
                        json_str = result_text[start_idx:end_idx]
                        parsed_data = json.loads(json_str)
                        events_data = parsed_data.get('events', [])
                    else:
                        events_data = []
                except json.JSONDecodeError:
                    events_data = []
            
        finally:
            # Restore original API key
            if original_key:
                os.environ['OPENAI_API_KEY'] = original_key
            elif 'OPENAI_API_KEY' in os.environ:
                del os.environ['OPENAI_API_KEY']
        
        return events_data

    def create_events_from_parsed_data(self, events_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create calendar events from parsed data"""
        created_events = []
        failed_events = []
        
        for event_data in events_data:
            try:
                # Validate required fields
                if not all(key in event_data for key in ["title", "start", "end", "timezone"]):
                    failed_events.append({
                        "event": event_data,
                        "error": "Missing required fields (title, start, end, timezone)"
                    })
                    continue
                
                # Create the event
                result = self.add_event_tool._run(
                    title=event_data["title"],
                    start=event_data["start"],
                    end=event_data["end"],
                    timezone=event_data["timezone"],
                    description=event_data.get("description"),
                    location=event_data.get("location"),
                    attendees=event_data.get("attendees")
                )
                
                created_events.append({
                    "title": event_data["title"],
                    "start": event_data["start"],
                    "end": event_data["end"],
                    "result": result
                })
                
            except Exception as e:
                failed_events.append({
                    "event": event_data,
                    "error": str(e)
                })
        
        return {
            "created_events": created_events,
            "failed_events": failed_events
        }

    def chat_with_calendar(self, messages: List[Dict[str, str]], openai_api_key: str) -> str:
        """Chat with calendar using CrewAI"""
        try:
            user_message = messages[-1]['content']
            
            # Set the OpenAI API key for the crew
            original_key = os.environ.get('OPENAI_API_KEY')
            os.environ['OPENAI_API_KEY'] = openai_api_key
            
            try:
                response = calendar_crew_run(user_message)
                if response is None:
                    response = "I'm here to help with your calendar! You can ask me about your events, schedule, or any calendar-related questions."
            except Exception as crew_error:
                print(f"Calendar crew error: {crew_error}")
                # Fallback response
                response = "I'm your calendar assistant! You can ask me about your events, schedule, or any calendar-related questions. What would you like to know?"
            finally:
                # Restore original API key
                if original_key:
                    os.environ['OPENAI_API_KEY'] = original_key
                elif 'OPENAI_API_KEY' in os.environ:
                    del os.environ['OPENAI_API_KEY']
            
            # Ensure response is a string
            if not isinstance(response, str):
                response = str(response) if response is not None else "I'm here to help with your calendar questions!"
            
            return response
            
        except Exception as e:
            print(f"Chat error: {e}")
            raise Exception("Error processing chat request")


# Create a global AI service instance
ai_service = AIService() 