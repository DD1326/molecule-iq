from .constraint_parser import parse_query
from .agent_coordinator import coordinate_agent
from .schemas import AgentResponse

class Translator:
    """
    Main Orchestrator tying the parser and coordinator together.
    """
    def __init__(self):
        pass

    def process_query(self, user_query: str, page_context: dict = None, chat_history: list = None) -> dict:
        # Step 1: Parse the user's natural language to structured constraints
        parsed_query = parse_query(user_query, chat_history=chat_history)

        # Step 2: Route to the appropriate agent (with history support from Account 2)
        agent_response = coordinate_agent(parsed_query, user_query, page_context=page_context, chat_history=chat_history)

        return {
            "intent": parsed_query.intent,
            "constraints": parsed_query.constraints.model_dump(),
            "reasoning": parsed_query.reasoning,
            "agent_response": agent_response.response,
            "source_agent": agent_response.source_agent,
            "activities": [a.model_dump() for a in agent_response.activities]
        }
