from langgraph.types import Command
from pycomponents.pynodes.schema import GraphState
from langgraph.graph import END
# from pycomponents.constants import GENERATESEARCHQUERIES

def process_supervisor(state: GraphState):
    print("---PROCESS SUPERVISOR---")
    websearchprompts = state.web_search_queries
    documents = state.documents
    graded_documents = state.graded_documents
    scenario_documents = state.scenario_documents


    if len(websearchprompts) == 0:
        goto = "GENERATESEARCHQUERIES"
        print('search queries')
    elif len(websearchprompts) > 1 and len(documents) == 0 :
        goto = "WEBSEARCH"
        # goto = END
    elif len(documents) > 0 and len(graded_documents)== 0:
        # print("----------")
        # print(documents)
        # print("----------")
        goto="DOCUMENTGRADER"
        # goto = END
    elif len(graded_documents)>0 and len(scenario_documents) == 0:
        # print("----------")
        # print(graded_documents)
        # print("----------")
        goto="GENERATESCENARIOS"
    elif len(scenario_documents)>0:
        # print("----------")
        # print(scenario_documents)
        # # print("Test")
        # print("----------")
        goto=END

    

    return Command(
        update={},
        goto=goto,
    )
