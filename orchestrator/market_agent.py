import os
from openai import OpenAI
from .schemas import ParsedQuery, AgentResponse

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "dummy"),
)
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")

def run_market_agent(parsed_query: ParsedQuery, raw_query: str, page_context: dict = None) -> AgentResponse:
    molecule = parsed_query.constraints.molecule_name or "this molecule"
    
    context_str = f"\nCURRENT PAGE DATA SCAN: {page_context}\n" if page_context else ""

    system_prompt = f"""
You are the MoleculeIQ Market Analysis & Global Intelligence Agent.
{context_str}
The user is asking about the commercial landscape or availability of a drug.

User's Query: "{raw_query}"
Identified Molecule: "{molecule}"
Hard Constraints: {parsed_query.constraints.model_dump()}

Your goal is to provide a detailed, markdown-formatted market report. 
Include (if known):
- Global market sizing or demand trends.
- Major manufacturers or dominant brand names.
- Pricing and accessibility notes.
- Supply chain logistics or recent shortages.
- Emerging pharmaceutical markets or regions.

Maintain a professional, data-centric tone with markdown summaries.
"""

    try:
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
            ],
            temperature=0.3,
            max_tokens=1024
        )
        content = response.choices[0].message.content
        return AgentResponse(response=content, source_agent="MoleculeIQ Market Intelligence")
    except Exception as e:
        return AgentResponse(
            response=f"Error running market agent: {e}",
            source_agent="MoleculeIQ Market Intelligence"
        )
