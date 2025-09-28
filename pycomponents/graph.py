from langgraph.graph import END, StateGraph, START

from pycomponents.pynodes.schema import GraphState

from pycomponents.constants import (
    SUPERVISOR, 
    WEBSEARCH, 
    GENERATESEARCHQUERIES,
    DOCUMENTGRADER,
    GENERATESCENARIOS
    )

from pycomponents.pynodes.generate_search_queries_node import generate_search_queries
from pycomponents.pynodes.supervisor_node import process_supervisor
from pycomponents.pynodes.websearch_node import web_search
from pycomponents.pynodes.document_grader_node import grade_documents
from pycomponents.pynodes.generate_scenarios_node import generate_risk_scenarios


builder = StateGraph(GraphState)

builder.add_node(SUPERVISOR, process_supervisor)
builder.add_node(WEBSEARCH, web_search)
builder.add_node(GENERATESEARCHQUERIES, generate_search_queries)
builder.add_node(DOCUMENTGRADER, grade_documents)
builder.add_node(GENERATESCENARIOS, generate_risk_scenarios)

builder.add_edge(START, SUPERVISOR)
# builder.add_edge(SUPERVISOR,GENERATESEARCHQUERIES)
# builder.add_edge(SUPERVISOR, WEBSEARCH)
# builder.add_edge(SUPERVISOR, DOCUMENTGRADER)

# builder.add_edge(GENERATESEARCHQUERIES, SUPERVISOR)
# builder.add_edge(WEBSEARCH, SUPERVISOR)
# builder.add_edge(DOCUMENTGRADER, SUPERVISOR)





quant_scenario_app = builder.compile()
