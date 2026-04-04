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
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-pro") 

def parse_query(user_query: str) -> ParsedQuery:
    """
    Parses a natural language query into a structured ParsedQuery object.
    """
    schema = ParsedQuery.model_json_schema()
    
    system_prompt = f"""
You are an intelligent constraint parser for a drug discovery platform called MoleculeIQ.
Your task is to analyze the user's natural language query and extract the intent and constraints.

Possible Intents:
- CDSCO_STATUS: User is asking about the regulatory status of a drug in India (e.g., "Is Paracetamol banned in India?")
- GENERAL_MOLECULE_SEARCH: User is asking for general information or repurposing opportunities for a molecule.
- CLINICAL_TRIAL_SEARCH: User is asking specifically about clinical trials.
- UNKNOWN: Any other queries.

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
