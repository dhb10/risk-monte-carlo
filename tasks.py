#celery -A celery_config worker --loglevel=debug

from dotenv import load_dotenv
load_dotenv()

from io import BytesIO, StringIO
import os
import re
import pandas as pd
import json
import textwrap
from pycomponents.graph import quant_scenario_app
from celery_config import celery_app

import traceback

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.units import inch
from reportlab.lib import colors

from azure.storage.blob import BlobServiceClient

###---ENV---###
blob_connection_string = os.getenv("BLOB_CONNECTION_STRING")
blob_container_name = os.getenv("BLOB_CONTAINER_RISKID")
blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
container_client = blob_service_client.get_container_client(blob_container_name)
blob_container_key=os.getenv("BLOB_CONTAINER_KEY")



# quant_scenario_app.invoke({"sector":"higher education", 'organization':'Northwestern University','risk':'cybersecurity'})



###---HELPER FUNCTIONS---###

def df_to_list_of_risk_dicts(df):
    return df.to_dict(orient='records')


def upload_to_blob(data, blob_name: str, is_binary: bool = False):
    blob_client = container_client.get_blob_client(blob_name)
    upload_data = data if is_binary else data.encode("utf-8")
    blob_client.upload_blob(upload_data, overwrite=True)
    print(f"Uploaded to blob: {blob_name}")


def upload_df_to_blob(df: pd.DataFrame, blob_name: str):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    upload_to_blob(csv_buffer.getvalue(), blob_name)

    import re

def clean_markdown_text(text, width=100):
    """
    Cleans up common markdown patterns, improves whitespace, 
    and reflows text for better paragraph readability.
    """
    # Remove markdown headers and formatting
    text = re.sub(r"#* *(\d*\.)?[\-\*]?", "", text)                  # Remove #, ##, ###, bullet points, numbered bullets
    text = re.sub(r"`+", "", text)                                   # Remove inline code marks
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)            # [text](link) -> text
    text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", r"\1", text)           # ![alt](img) -> alt
    text = re.sub(r"---+", "", text)                                 # Remove HRs
    
    # Replace multiple newlines/tabs with a single blank line
    text = re.sub(r"[\n\r]{3,}", "\n\n", text)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n[ \t]+\n', '\n\n', text)                       # Blank lines w/ spaces -> blank line
    text = re.sub(r'\n{2,}', '\n\n', text)                           # Multiple blank lines to just two
    
    # Strip start/end whitespace
    text = text.strip()
    
    # === Line reflow step for paragraph-like look ===
    # Only reflow if the paragraph is long enough (avoid mangling single-line lists, etc)
    paragraphs = [p.strip() for p in text.split('\n\n')]
    reflowed = "\n\n".join(textwrap.fill(p, width=width) for p in paragraphs if p)
    
    return reflowed


def clean_contents_in_results(results):
    """
    Traverses your results data structure and cleans the "content" key in each document found under
    results['documents'], results['graded_documents'], and results['scenario_documents'].
    Handles lists of risks at the top-level.
    """
    # Support both top-level list of risks and a single result dict
    risks = results if isinstance(results, list) else [results]
    
    doc_keys = ["documents", "graded_documents", "scenario_documents"]

    for risk_result in risks:
        try:
            containers = risk_result.get("results", risk_result)
        except AttributeError:
            continue
        for key in doc_keys:
            docs = containers.get(key, [])
            for doc in docs:
                if "content" in doc and isinstance(doc["content"], str):
                    doc["content"] = clean_markdown_text(doc["content"])
                # If "scenarios" are nested and you want to clean those too, do something similar here

    return results  # modifies in-place, also returned for convenience


def generate_risk_pdf(risk_data) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    story = []

    header_style = styles["Heading2"]
    body_style = styles["BodyText"]
    bullet_style = ParagraphStyle(
        name='Bullet',
        parent=styles['BodyText'],
        bulletIndent=0,
        leftIndent=15,
        spaceBefore=3,
    )

    for item in risk_data:
        risk_json = list(item.values())[0]
        risk = json.loads(risk_json)

        story.append(Paragraph(risk["parent_risk"], header_style))
        story.append(Spacer(1, 6))

        story.append(Paragraph(risk["definition"], body_style))
        story.append(Spacer(1, 6))

        bullets = [ListItem(Paragraph(reason, bullet_style)) for reason in risk["reasoning"]]
        story.append(ListFlowable(bullets, bulletType='bullet', start='bulletchar'))

        story.append(Spacer(1, 12))
        story.append(Paragraph("<hr width='100%' color='gray'/>", body_style))
        story.append(Spacer(1, 12))

    doc.build(story)
    buffer.seek(0)
    return buffer



###---TASKS---###

#wrap the major celery task functions in a try/except that logs/prints all details before re-raising, it saves sooo much time
#celery -A celery_config worker --loglevel=debug
@celery_app.task(acks_late=True)
def generate_scenarios(risk_dict: dict):
    # Construct a FRESH state: only pass in risk/meta fields and *empty* other lists!
    clean_state = {
        "sector": risk_dict.get("sector", ""),
        "organization": risk_dict.get("organization", ""),
        "risk": risk_dict.get("risk_name", ""),  # or "risk", whatever your schema is
        "web_search_queries": [],
        "documents": [],
        "graded_documents": [],
        "scenario_documents": [],
    }
    print("Invoking with state:", clean_state)
    result = quant_scenario_app.invoke(clean_state)
    return {
        "risk_name": risk_dict.get("risk_name", ""),
        "risk_definition": risk_dict.get("risk_definition", ""),
        "results": result
    }
        


@celery_app.task()
def chord_callback(results):
    # results: List of per-risk dictionaries from generate_scenarios
    print(f"Received list of {len(results)} risk analysis results")
    print("*********")
    print(results)
    print("*********")

    cleaned_results = clean_contents_in_results(results)

    # return cleaned_results
    return results