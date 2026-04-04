from pydantic import BaseModel, Field
from typing import Optional

class Constraints(BaseModel):
    molecule_name: Optional[str] = Field(None, description="The name of the drug or molecule, e.g. Metformin, Paracetamol")
    disease_status: Optional[str] = Field(None, description="The disease or condition being treated")
    region: Optional[str] = Field(None, description="The geographical region referenced, e.g. India, US")
    regulatory_status: Optional[str] = Field(None, description="Status like Banned, Approved, Experimental")

class ParsedQuery(BaseModel):
    intent: str = Field(..., description="Main intent: 'CDSCO_STATUS', 'GENERAL_MOLECULE_SEARCH', 'CLINICAL_TRIAL_SEARCH', 'PATENT_SEARCH', 'MARKET_SEARCH', or 'UNKNOWN'")
    constraints: Constraints = Field(..., description="Extracted entities and constraints from the query")
    reasoning: str = Field(..., description="Short explanation of why this intent was selected based on the user query")

class AgentResponse(BaseModel):
    response: str = Field(..., description="The final markdown flavored response intended for the user")
    source_agent: str = Field(..., description="The name of the agent that handled this query")
