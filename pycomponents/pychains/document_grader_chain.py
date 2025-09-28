from dotenv import load_dotenv
load_dotenv()

import os

from langchain_openai import AzureChatOpenAI
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.prompts import  ChatPromptTemplate

azure_openai_api_key = os.getenv("AZUREOPENAI_API_KEY")
azure_openai_endpoint = os.getenv("AZUREOPENAI_ENDPOINT")


llm = AzureChatOpenAI(
            model="BT-RiskScan-Model-DEV-USE-2",
            openai_api_key=azure_openai_api_key,
            api_version="2024-10-01-preview",  
            azure_endpoint=azure_openai_endpoint
        )

###---STRUCTURED OUTPUT---###

#the LangChain LLM returns an AIMessage object not a plain string
def boolean_parser(output) -> bool:
    if hasattr(output, "content"):
        out_str = output.content
    else:
        out_str = str(output)
    return out_str.strip().lower().startswith("true")
    

document_grader_template = """
You are an expert risk quantification analyst.

Given the following information:
- Risk: {risk}
- Sector: {sector}
- Organization: {organization}
- Document: {document}

Your task is to determine if the provided document contains enough information to generate a list of plausible risk scenarios that could impact the organization. These scenarios should be based on incidents of the specified risk that have occurred in the sector or are specific to the organization.

A document contains "enough information" if it describes actual incidents, events, or situations related to the risk, either in the sector or at the organization, that could be used to construct detailed risk scenarios (e.g., ransomware attacks, data breaches, regulatory fines, etc.).

Respond with only a single word: "True" if the document contains enough information, or "False" if it does not.
"""

supervisor_prompt = ChatPromptTemplate.from_messages([
      ("system","You are an expert risk quantification analyst."),
      ("human", document_grader_template)
])

document_grader_chain = (
    RunnablePassthrough() 
    | supervisor_prompt
    | llm 
    | RunnableLambda(boolean_parser)
)