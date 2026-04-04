from pydantic import BaseModel, Field
from typing import Optional, List

class Constraints(BaseModel):
    molecule_name: Optional[str] = Field(None, description="The name of the drug or molecule, e.g. Metformin, Paracetamol")
    disease_status: Optional[str] = Field(None, description="The clinical unmet need, objective, or disease condition being treated")
    region: Optional[str] = Field(None, description="The geographical region referenced, e.g. India, US")
    regulatory_status: Optional[str] = Field(None, description="Regulatory status required, like Approved, Banned, or Phase 3")
    exclusions: Optional[str] = Field(None, description="Specific things to avoid or exclude, e.g. 'cardiovascular toxicity', 'pediatrics', 'high cost'")
    price_requirement: Optional[str] = Field(None, description="Budgetary or cost constraints, e.g. 'low cost', 'affordable'")

class ParsedQuery(BaseModel):
    intent: str = Field(..., description="Main intent: 'CDSCO_STATUS', 'GENERAL_MOLECULE_SEARCH', 'CLINICAL_TRIAL_SEARCH', 'PATENT_SEARCH', 'MARKET_SEARCH', or 'UNKNOWN'")
    constraints: Constraints = Field(..., description="Extracted entities and constraints from the query")
    reasoning: str = Field(..., description="Short explanation of why this intent was selected based on the user query")

class AgentActivity(BaseModel):
    agent: str = Field(..., description="Name of the agent, e.g. 'Clinical', 'Patent', 'Market'")
    action: str = Field(..., description="The action being performed, e.g. 'Scanning Banned Drugs', 'Checking USPTO'")
    status: str = Field(..., description="Status of the action: 'searching', 'found', 'done', or 'error'")

class AgentResponse(BaseModel):
    response: str = Field(..., description="The final markdown flavored response intended for the user")
    source_agent: str = Field(..., description="The name of the agent that handled this query")
    activities: List[AgentActivity] = Field(default_factory=list, description="List of background activities performed by agents")
