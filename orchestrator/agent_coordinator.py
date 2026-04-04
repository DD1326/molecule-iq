import os
from openai import OpenAI
from .schemas import ParsedQuery, AgentResponse
from .cdsco_agent import run_cdsco_agent

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "dummy"),
)
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-pro")

def run_general_agent(parsed_query: ParsedQuery, raw_query: str) -> AgentResponse:
    molecule = parsed_query.constraints.molecule_name or "this molecule"
    
    system_prompt = f"""
You are the MoleculeIQ General Intelligence Agent.
The user is asking a question about a drug or pharmaceutical molecule.

User's Query: "{raw_query}"
Identified Molecule: "{molecule}"

Provide a highly informative, structured response in Markdown. Give biological mechanisms, 
repurposing history, or clinical significance. Keep it scientifically accurate but accessible.
"""

    try:
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
            ],
            temperature=0.4,
            max_tokens=1024
        )
        content = response.choices[0].message.content
        return AgentResponse(response=content, source_agent="MoleculeIQ Core Intelligence")
    except Exception as e:
        return AgentResponse(
            response=f"Error running General agent: {e}",
            source_agent="MoleculeIQ Core Intelligence"
        )

def coordinate_agent(parsed_query: ParsedQuery, raw_query: str) -> AgentResponse:
    """
    Routes the parsed query to the appropriate specialized agent.
    """
    if parsed_query.intent == "CDSCO_STATUS":
        return run_cdsco_agent(parsed_query, raw_query)
    elif parsed_query.intent in ["GENERAL_MOLECULE_SEARCH", "CLINICAL_TRIAL_SEARCH"]:
        return run_general_agent(parsed_query, raw_query)
    else:
        # Fallback to general agent
        return run_general_agent(parsed_query, raw_query)
