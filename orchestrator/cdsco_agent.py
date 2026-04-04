import os
import csv
from openai import OpenAI
from .schemas import ParsedQuery, AgentResponse
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "dummy"),
)
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")

def run_cdsco_agent(parsed_query: ParsedQuery, raw_query: str, page_context: dict = None) -> AgentResponse:
    molecule = parsed_query.constraints.molecule_name or "this molecule"
    
    # ── HARD DATA LOOKUP ──
    csv_path = os.path.join(os.path.dirname(__file__), 'cdsco_status_2026.csv')
    csv_status = None
    if os.path.exists(csv_path):
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if molecule.lower() in row['DrugName'].lower() or row['DrugName'].lower() in molecule.lower():
                    csv_status = row
                    break

    context_str = f"\nCURRENT PAGE DATA SCAN: {page_context}\n" if page_context else ""
    
    status_hint = f"\nVERIFIED DATABASE MATCH: {csv_status}\n" if csv_status else ""

    system_prompt = f"""
You are the CDSCO Regulatory Intelligence Agent.
{context_str}
{status_hint}
The user is asking about the regulatory status of a drug in India at the CDSCO level.

User's Query: "{raw_query}"
Identified Molecule: "{molecule}"

Your goal is to provide the OFFICIAL regulatory status (BANNED, APPROVED, or RESTRICTED).
If there is a VERIFIED DATABASE MATCH above, prioritize that info as Hard Fact.
If not, synthesize the status based on your medical training for the Indian market.

Structure your response:
1.  **📊 CDSCO STATUS**: [APPROVED/BANNED/RESTRICTED]
2.  **📋 Category**: [Indication]
3.  **⚖️ Regulatory Context**: [Reasoning]
4.  **💡 Innovation Insight**: [Is this good for repurposing?]
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
