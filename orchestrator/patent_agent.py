import os
from openai import OpenAI
from .schemas import ParsedQuery, AgentResponse

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "dummy"),
)
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash")

def run_patent_agent(parsed_query: ParsedQuery, raw_query: str) -> AgentResponse:
    molecule = parsed_query.constraints.molecule_name or "this molecule"
    
    system_prompt = f"""
You are the MoleculeIQ Patent & Exclusivity Intelligence Agent.
The user is asking about the patent landscape, exclusivity, or lifecycle management of a drug.

User's Query: "{raw_query}"
Identified Molecule: "{molecule}"

Your goal is to provide a detailed, markdown-formatted patent report. 
Include (if known):
- Historical patent expiration dates.
- Orange Book exclusivity status (Hatch-Waxman).
- Potential for 505(b)(2) regulatory pathways.
- Recent patent litigation or brand name transitions.

Keep the response highly structured with bullet points. Cite sources like 'USPTO' or 'Orange Book' when applicable.
"""

    try:
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
            ],
            temperature=0.3
        )
        content = response.choices[0].message.content
        return AgentResponse(response=content, source_agent="MoleculeIQ Patent Intelligence")
    except Exception as e:
        return AgentResponse(
            response=f"Error running patent agent: {e}",
            source_agent="MoleculeIQ Patent Intelligence"
        )
