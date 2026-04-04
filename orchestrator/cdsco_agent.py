import os
from openai import OpenAI
from .schemas import ParsedQuery, AgentResponse
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "dummy"),
)
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-pro")

def run_cdsco_agent(parsed_query: ParsedQuery, raw_query: str) -> AgentResponse:
    molecule = parsed_query.constraints.molecule_name or "this molecule"
    
    # In a real scenario, this is where we would query a CDSCO csv or API
    # For now, we will ask the LLM to generate a plausible regulatory status 
    # response acting as the CDSCO intelligence engine.
    
    system_prompt = f"""
You are the CDSCO Regulatory Intelligence Agent within the MoleculeIQ platform.
The user is asking about the regulatory status of a drug in India.

User's Query: "{raw_query}"
Identified Molecule: "{molecule}"

Respond in Markdown format. Keep the answer professional, concise, and structured. 
If you aren't 100% sure, provide the most likely regulatory status (Approved, Restricted, Banned) 
based on general medical knowledge, but state that this is an AI synthesis.
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
        return AgentResponse(response=content, source_agent="CDSCO Regulatory Intelligence")
    except Exception as e:
        return AgentResponse(
            response=f"Error running CDSCO agent: {e}",
            source_agent="CDSCO Regulatory Intelligence"
        )
