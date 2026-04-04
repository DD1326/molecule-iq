import os
import json
from openai import OpenAI
from .schemas import ParsedQuery, Constraints
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "dummy"),
)

# You can change the model based on what you want to use via OpenRouter
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")

def parse_query(user_query: str, chat_history: list = None) -> ParsedQuery:
    """
    Parses a natural language query into a structured ParsedQuery object.
    Includes Conversational State Management memory.
    """
    schema = ParsedQuery.model_json_schema()
    
    history_str = ""
    if chat_history:
        history_str = "\nPREVIOUS CONVERSATION HISTORY:\n"
        for msg in chat_history[-10:]:
            history_str += f"- {msg['role'].upper()}: {msg['content']}\n"
    
    system_prompt = f"""
You are an intelligent constraint parser for a drug discovery platform called MoleculeIQ.
Your task is to analyze the user's natural language query and extract the intent and "Hard Agent Constraints." 
A Hard Agent Constraint is a non-negotiable filter or specific requirement such as an exclusion (e.g., "gentler on the heart" -> exclude: cardiovascular toxicity).

{history_str}
You MUST use the conversation history above to maintain Conversational State Management. If the user refers to past context (e.g., "reject that candidate", "find one without this effect"), you must translate it into constraints.

If the user feedback is extremely ambiguous, autonomously return UNKNOWN intent so the orchestrator can ask clarifying questions before re-tasking agents.

Possible Intents:
- CDSCO_STATUS: User is asking about the regulatory status of a drug in India (CDSCO).
- PATENT_SEARCH: User is asking about drug patents, expiration, or 505(b)(2) pathways.
- MARKET_SEARCH: User is asking about market size, pricing, or supply chain.
- GENERAL_MOLECULE_SEARCH: User is asking for general informational or repurposing history.
- CLINICAL_TRIAL_SEARCH: User is asking about clinical trial data or status.
- UNKNOWN: Any other unrelated queries, or when proactive clarification is needed.

You MUST return a raw JSON object matching this schema, completely without markdown wrappers:
{json.dumps(schema, indent=2)}
"""

    try:
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=1024
        )
        
        json_str = response.choices[0].message.content
        parsed_dict = json.loads(json_str)
        return ParsedQuery(**parsed_dict)
    except Exception as e:
        print(f"[Parser Error] {e}")
        # Fallback
        return ParsedQuery(
            intent="UNKNOWN",
            constraints=Constraints(),
            reasoning="Failed to parse via LLM."
        )
