from typing import Any, Dict
from pycomponents.pynodes.schema import GraphState
from pycomponents.pychains.document_grader_chain import document_grader_chain
from langgraph.types import Command
from langgraph.graph import END

def grade_documents(state: GraphState) -> Dict[str, Any]:
    print("---DOCUMENT GRADER---")
    sector = state.sector
    organization = state.organization
    risk = state.risk
    documents = state.documents
    graded_documents = []

    # print("********")
    # print(documents)
    # print("********")

    for doc in documents:

        content = doc.get('content', '')
        if not content:
            continue
        inputs = {
            "sector": sector,
            "organization": organization,
            "risk": risk,
            "document": content,
        }
        # print(f"INPUT TO GRADER: {inputs!r}") #!r to access repr() for debugging
        is_relevant = document_grader_chain.invoke(inputs)
        print(f"IS RELEVANT: {is_relevant}")
        if is_relevant:
            graded_documents.append(doc)  # full metadata preserved

    # state.graded_documents = graded_documents

    # print("###############")
    # print(graded_documents)
    # print("###############")

    return Command(
        update={"graded_documents": graded_documents},
        goto="SUPERVISOR",
    )


    {
        'query': ...,
        'follow_up_questions': ...,
        'answer': ...,
        'images': ...,
        'results': [ ... ],  # <--- THIS is a list of document dicts
        'response_time': ...,
        'request_id': ...
    }

    {
        'url': ...,
        'title': ...,
        'content': ...,   # <--- THIS is the document content you want
        'score': ...,
        'raw_content': ...
    }
    
    
