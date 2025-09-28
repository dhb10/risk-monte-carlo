from typing import Any, Dict
from pycomponents.pynodes.schema import GraphState
from pycomponents.pychains.generate_queries_chain import generate_search_queries_chain
from langgraph.types import Command


def generate_search_queries(state: GraphState) -> Dict[str,Any]:
    print("---GENERATE SEARCH QUERIES---")
    sector = state.sector
    organization = state.organization
    risk = state.risk
    
    queries = generate_search_queries_chain.invoke({"sector":sector,"organization":organization,"risk":risk})

    print(queries)

    if isinstance(queries, list):
        state.web_search_queries.extend(queries)
    else:
        raise ValueError("Expected a list of queries, got something else.")

    return Command(
        update={"web_search_queries": state.web_search_queries},
        goto="SUPERVISOR",
    )