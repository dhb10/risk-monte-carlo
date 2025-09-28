from dotenv import load_dotenv
load_dotenv()

import os
import datetime
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
import ast



azure_openai_api_key = os.getenv("AZUREOPENAI_API_KEY")
azure_openai_endpoint = os.getenv("AZUREOPENAI_ENDPOINT")


llm = AzureChatOpenAI(
            model="BT-RiskScan-Model-DEV-USE-2",
            openai_api_key=azure_openai_api_key,
            api_version="2024-10-01-preview",  
            azure_endpoint=azure_openai_endpoint
        )


def format_as_python_literal(output):
    #if output is AIMessage get content, else str
    if hasattr(output, "content"):
        output = output.content
    try:
        return ast.literal_eval(output)
    except Exception as e:
        # Optionally, log or handle the error
        raise ValueError(f"Failed to parse output as dictionary: {output}")
    

scenario_identification_prompt_template = """
You are a risk quantification expert.

Given the following information:
Sector: {sector}
Organization: {organization}
Risk of interest: {risk}
Document: {document}
Current Date: {current_date}

Task:
Carefully read the document.
Identify and extract all distinct, quantifiable risk scenarios described or implied in the document that relate to the specified risk.
For each scenario:
- First, provide the reasoning for why this scenario was identified, referencing specific information or implications from the document.
- Then, clearly state the risk scenario itself.
Each scenario should be specific, actionable, and relevant to the risk and organization (e.g., "A ransomware attack encrypts company records, requiring payment for access").
Focus on scenarios that could plausibly impact {organization}, referencing incidents in {sector} or specific to {organization} if available.
Output your answer as a Python list of dictionaries, each with two keys:
    - "reasoning": A brief explanation of why this scenario was identified, based on the document.
    - "scenario": The scenario description (as a string).

Output format:
[
  {{"reasoning": "<reasoning for scenario 1>", "scenario": "<scenario 1>"}},
  {{"reasoning": "<reasoning for scenario 2>", "scenario": "<scenario 2>"}},
  ...
]

Only output the list of dictionaries, with no extra commentary.
"""

scenario_search_prompt = PromptTemplate.from_template(scenario_identification_prompt_template).partial(
    current_date=lambda: datetime.datetime.now().strftime("%Y-%m-%d"),
)

generate_scenarios_chain = (
    RunnablePassthrough() 
    | scenario_search_prompt 
    | llm 
    | format_as_python_literal
)