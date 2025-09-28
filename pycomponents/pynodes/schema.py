from typing import List, Annotated, Optional
from pydantic import BaseModel, Field
from operator import add


class GraphState(BaseModel):
    sector: str
    organization: str
    risk: str = Field(
        description = "The current risk that we are identifying scenarios for.",
        default=""
    )

    web_search_queries: Optional[List[str]] = Field(
        description = "List of the generated search queries, multiple list if the supervisor determines additional information is needed.",
        default_factory=list
    )

    documents: Optional[List[dict]] = Field(
        description = "The search results documents used to generate the LLM analysis.",
        default_factory=list
    )

    graded_documents: Optional[List[dict]] = Field(
        description = "The graded list of documents used to generate the scenarios.",
        default_factory=list
    )

    scenario_documents: Optional[List[dict]] = Field(
        description = "The graded documents list of dictionaries with a 'scenarios' key, which is a list of dictionaries with a 'reasoning' key and a 'scenario' key.",
        default_factory=list
    )


