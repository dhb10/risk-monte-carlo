from dotenv import load_dotenv
load_dotenv()

import os
import datetime
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.runnables import RunnableSequence, RunnablePassthrough
from langchain_core.prompts import PromptTemplate
import ast
import re



azure_openai_api_key = os.getenv("AZUREOPENAI_API_KEY")
azure_openai_endpoint = os.getenv("AZUREOPENAI_ENDPOINT")


llm = AzureChatOpenAI(
            model="BT-RiskScan-Model-DEV-USE-2",
            openai_api_key=azure_openai_api_key,
            api_version="2024-10-01-preview",  
            azure_endpoint=azure_openai_endpoint
        )

def format_as_list(output):
    # Try to get to content if structured as LLM output
    if hasattr(output, "content"):
        output = output.content

    # Remove code block markers if present
    output = output.strip()
    output = re.sub(r"^```(?:python)?", "", output)
    output = re.sub(r"```$", "", output)
    output = output.strip()

    # Strip stuff before the first bracket if accidentally included
    output = re.sub(r"^[^\[]*", "", output)

    try:
        result = ast.literal_eval(output)
        if not isinstance(result, list):
            raise ValueError("Output is not a list: " + str(type(result)))
        return result
    except Exception as e:
        raise ValueError(f"Error parsing output as list: {output}\nError: {e}")


scenario_search_prompt_template = """
You are a senior enterprise risk management researcher. Your specialty is identifying and generating highly targeted search queries that uncover the top-known risk scenarios for organizations, with a focus on risk exposure based on sector, organization name, and a specified risk type.

Given the sector, the organization name, the risk of interest, and the current date, generate exactly five detailed search queries designed to surface real-world scenarios in which the specified risk has impacted similar organizations or could impact the given organization now.

- Your queries should help uncover current or recent incidents, publications, or analysis related to the risk exposure.
- The first three queries should focus broadly on the sector, uncovering notable scenarios or case studies related to this type of risk within similar organizations.
- The final two queries should be tailored to the specific organization, uncovering incidents, events, or published analyses (including news, regulatory filings, or university bulletins, if applicable) relevant to the given risk, as recent as possible.
- All search queries should aim to surface practical, scenario-based information (not just statistics or general summaries).
- Use the current date to guide your focus towards recent and relevant sources.
- The output should be in the form of a Python list (no explanations or markdown/code block formatting).

Sector: {sector}
Organization: {organization}
Risk: {risk}
Current Date: {current_date}

Generate exactly five search queries as described. Your queries should help identify real scenarios for risk exposure for the organization and sector in question.
"""

scenario_search_prompt = PromptTemplate.from_template(scenario_search_prompt_template).partial(
    current_date=lambda: datetime.datetime.now().strftime("%Y-%m-%d"),
)

generate_search_queries_chain = (
    RunnablePassthrough() 
    | scenario_search_prompt 
    | llm 
    | format_as_list
)