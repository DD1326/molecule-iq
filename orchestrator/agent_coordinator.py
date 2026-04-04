import os
from openai import OpenAI
from .schemas import ParsedQuery, AgentResponse
from .cdsco_agent import run_cdsco_agent
from .patent_agent import run_patent_agent
from .market_agent import run_market_agent

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "dummy"),
)
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash")

def run_general_agent(parsed_query: ParsedQuery, raw_query: str, page_context: dict = None) -> AgentResponse:
    molecule = parsed_query.constraints.molecule_name or "this molecule"
    
    context_str = f"\nCURRENT PAGE DATA SCAN: {page_context}\n" if page_context else ""

    system_prompt = f"""
You are the MoleculeIQ General Intelligence Agent.
The user is asking a question about a drug or pharmaceutical molecule.

{context_str}

User's Query: "{raw_query}"
Identified Molecule: "{molecule}"
Hard Constraints: {parsed_query.constraints.model_dump()}

Your goal is to answer the user's query thoughtfully. 

INLINE CARDS:
If you propose a specific drug candidate for repurposing, you MUST provide a "Candidate Card" summary at the end of your response using this EXACT format:
[CANDIDATE: Drug Name | Drug Class | Repurposing Status (e.g. Phase 2) | Key Bio-Mechanism or Insight]

Example: [CANDIDATE: Metformin | Biguanide | Phase 3 for Aging | AMPK Activator with anti-inflammatory properties]

If 'CURRENT PAGE DATA SCAN' is provided above, refer to it for accuracy.
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

def coordinate_agent(parsed_query: ParsedQuery, raw_query: str, page_context: dict = None) -> AgentResponse:
    """
    Routes the parsed query to the appropriate specialized agent.
    """
    if parsed_query.intent == "CDSCO_STATUS":
        return run_cdsco_agent(parsed_query, raw_query, page_context=page_context)
    elif parsed_query.intent == "PATENT_SEARCH":
        return run_patent_agent(parsed_query, raw_query, page_context=page_context)
    elif parsed_query.intent == "MARKET_SEARCH":
        return run_market_agent(parsed_query, raw_query, page_context=page_context)
    elif parsed_query.intent in ["GENERAL_MOLECULE_SEARCH", "CLINICAL_TRIAL_SEARCH"]:
        return run_general_agent(parsed_query, raw_query, page_context=page_context)
    else:
        # Fallback to general agent
        return run_general_agent(parsed_query, raw_query, page_context=page_context)
