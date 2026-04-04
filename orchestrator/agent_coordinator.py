import os
import concurrent.futures
from openai import OpenAI
from .schemas import ParsedQuery, AgentResponse, AgentActivity
from .cdsco_agent import run_cdsco_agent
from .patent_agent import run_patent_agent
from .market_agent import run_market_agent

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "dummy"),
)
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash")

def run_general_agent(parsed_query: ParsedQuery, raw_query: str, page_context: dict = None, chat_history: list = None, activities: list = None) -> AgentResponse:
    molecule = parsed_query.constraints.molecule_name or "this molecule"
    
    context_str = f"\nCURRENT PAGE DATA SCAN: {page_context}\n" if page_context else ""
    
    history_str = ""
    if chat_history:
        history_str = "\nPREVIOUS CONVERSATION HISTORY:\n"
        for msg in chat_history[-6:]:  # Only last 6 messages
            history_str += f"- {msg['role'].upper()}: {msg['content']}\n"

    system_prompt = f"""
You are the MoleculeIQ General Intelligence Agent.
The user is asking a question about a drug or pharmaceutical molecule.

{context_str}
{history_str}

User's Query: "{raw_query}"
Identified Molecule: "{molecule}"
Hard Constraints: {parsed_query.constraints.model_dump()}

Your goal is to answer the user's query thoughtfully, taking into account any previous context or constraints discussed in the chat history.

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
            max_tokens=512 # Lowered from 1024 to bypass 402 credit errors
        )
        content = response.choices[0].message.content
        return AgentResponse(
            response=content, 
            source_agent="MoleculeIQ Core Intelligence",
            activities=activities or []
        )
    except Exception as e:
        return AgentResponse(
            response=f"Error running General agent: {e}",
            source_agent="MoleculeIQ Core Intelligence",
            activities=activities or []
        )

def coordinate_multi_agent(parsed_query: ParsedQuery, raw_query: str, page_context: dict = None, chat_history: list = None) -> AgentResponse:
    """
    Coordinates Clinical, Patent, and Market agents in parallel for a comprehensive scan.
    """
    activities = []
    
    # Define tasks for parallel execution
    tasks = {
        "Clinical": lambda: run_cdsco_agent(parsed_query, raw_query, page_context),
        "Patent": lambda: run_patent_agent(parsed_query, raw_query, page_context),
        "Market": lambda: run_market_agent(parsed_query, raw_query, page_context)
    }

    results = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_agent = {executor.submit(func): name for name, func in tasks.items()}
        for future in concurrent.futures.as_completed(future_to_agent):
            agent_name = future_to_agent[future]
            try:
                res = future.result()
                results[agent_name] = res.response
                activities.append(AgentActivity(agent=agent_name, action=f"Analyzed {agent_name} data", status="done"))
            except Exception as e:
                activities.append(AgentActivity(agent=agent_name, action=f"Failed analysis", status="error"))

    # Synthesize the final response using the General Agent with the gathered intelligence
    full_intel_query = f"""
I have gathered specialized intelligence:

CLINICAL INTEL:
{results.get('Clinical', 'No data')}

PATENT INTEL:
{results.get('Patent', 'No data')}

MARKET INTEL:
{results.get('Market', 'No data')}

User's Original Question: {raw_query}

Please provide a master synthesis report using the specialized data above.
"""
    return run_general_agent(parsed_query, full_intel_query, page_context, chat_history=chat_history, activities=activities)

def coordinate_agent(parsed_query: ParsedQuery, raw_query: str, page_context: dict = None, chat_history: list = None) -> AgentResponse:
    """
    Routes the parsed query to the appropriate specialized agent or multi-agent scanner.
    """
    # ── For research-heavy queries, trigger the Multi-Agent Scanner ──
    if parsed_query.intent in ["GENERAL_MOLECULE_SEARCH", "CLINICAL_TRIAL_SEARCH"]:
        return coordinate_multi_agent(parsed_query, raw_query, page_context, chat_history=chat_history)
    
    # ── Specific intent routing ──
    if parsed_query.intent == "CDSCO_STATUS":
        res = run_cdsco_agent(parsed_query, raw_query, page_context=page_context)
        res.activities = [AgentActivity(agent="Clinical", action="Checked CDSCO Status", status="done")]
        return res
    elif parsed_query.intent == "PATENT_SEARCH":
        res = run_patent_agent(parsed_query, raw_query, page_context=page_context)
        res.activities = [AgentActivity(agent="Patent", action="Scanning Patent Portfolio", status="done")]
        return res
    elif parsed_query.intent == "MARKET_SEARCH":
        res = run_market_agent(parsed_query, raw_query, page_context=page_context)
        res.activities = [AgentActivity(agent="Market", action="Analyzing Market Dynamics", status="done")]
        return res
    else:
        # Fallback to general agent
        return run_general_agent(parsed_query, raw_query, page_context=page_context, chat_history=chat_history)
