from typing import Any, Dict
from pycomponents.pynodes.schema import GraphState
from pycomponents.pychains.generate_scenarios_chain import generate_scenarios_chain
from langgraph.types import Command
import re
import json

def strip_code_block(s):
    """
    Removes code block markers from LLM output.
    """
    # Remove triple backticks and optional 'python' language specifier
    return re.sub(r'^```(?:python)?\n?|```$', '', s.strip())

def parse_llm_json(s):
    return json.loads(strip_code_block(s))


def generate_risk_scenarios(state: GraphState) -> Dict[str,Any]:
    print("---GENERATE RISK SCENARIOS---")
    sector = state.sector
    organization = state.organization
    risk = state.risk
    documents = state.graded_documents
    scenario_documents = []

    for doc in documents:
        scenarios = generate_scenarios_chain.invoke({
            "sector": sector,
            "organization": organization,
            "risk": risk,
            "document": doc
        })
        # PATCH: If LLM output is string, clean/parse it:
        if isinstance(scenarios, str):
            try:
                scenarios = parse_llm_json(scenarios)
            except Exception as e:
                print(f"ERROR: Could not parse LLM scenarios output: {scenarios}")
                raise
        doc['scenarios'] = scenarios
        scenario_documents.append(doc)

    if isinstance(scenario_documents, list):
        state.scenario_documents.extend(scenario_documents)
    else:
        raise ValueError("Expected a list, got something else.")

    return Command(
        update={"scenario_documents": state.scenario_documents},
        goto="SUPERVISOR",
    )