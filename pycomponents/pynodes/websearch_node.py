import os
from dotenv import load_dotenv
load_dotenv()

from typing import Any, Dict
from langchain_tavily import TavilySearch
from pycomponents.pynodes.schema import GraphState
from langgraph.types import Command

# Initialize Tavily API wrapper

web_search_tool = TavilySearch(
    # max_results=5, 
    max_results=2,             
    include_answer=True,        #test this is it providing what we need
    include_raw_content=False,
    search_depth="advanced"
)

def web_search(state: GraphState):
    print("---WEB SEARCH---")
    search_queries = state.web_search_queries
    all_documents = []

    for q in search_queries:
        response = web_search_tool.invoke({"query": q})  # This is a dict!
        # print("##########")
        # print(response)
        # print("##########")
        # Top-level answer (could also be interesting to store, if needed)
        # answer = response.get("answer")
        # if answer:
        #     all_documents.append({
        #         "title": None,
        #         "url": None,
        #         "answer": answer,
        #         "search_query": q
        #     })
        
        # Now iterate properly over the results:
        results = response.get("results", [])
        for d in results:
            # print('result item:', d)
            result = {
                "search_query": q,
                "title": d.get("title"),
                "url": d.get("url"),
                "content": d.get("content", ""),
                
            }
            all_documents.append(result)

    #dedupe by url

    # print("***************")
    # print(all_documents)
    # print("***************")

    seen = set()
    deduped = []
    for d in all_documents:
        if d["url"] not in seen:
            deduped.append(d)
            seen.add(d["url"])
        else:
            print("Url already in docs")

    # print("***************")
    # print(deduped)
    # print("***************")

    state.documents.extend(deduped)

    print(f"---WEB SEARCH DONE: {len(deduped)} unique documents found---")

    return Command(
            update={"documents": state.documents},
            goto="SUPERVISOR",
        )
