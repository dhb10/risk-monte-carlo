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

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.enums import TA_LEFT

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


def generate_risk_scenarios_pdf(risk_data) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    header_style = styles["Heading2"]
    section_header = ParagraphStyle('section_header', parent=styles['Heading3'], textColor="#2563eb")
    bold_style = ParagraphStyle('Bold', parent=styles['BodyText'], fontName='Helvetica-Bold')
    scenario_style = styles['BodyText']

    footnotes = []
    content_footnote_map = {}
    next_footnote = 1

    story = []

    for risk in risk_data:
        story.append(Paragraph(risk["risk_name"], header_style))
        story.append(Paragraph(risk.get("risk_definition", ""), styles['BodyText']))
        story.append(Spacer(1, 10))

        docs = risk.get('results', {}).get('scenario_documents', [])
        for source in docs:
            # LINK and Title
            story.append(Paragraph(f'<b>LINK:</b> <a href="{source["url"]}">{source["title"]}</a>', section_header))

            # Query with footnote at the end
            query_text = f'<b>Query:</b> {source.get("search_query", "")}'
            content = source.get("content", "")
            footvalue = None
            if content:
                if content not in content_footnote_map:
                    content_footnote_map[content] = next_footnote
                    footnotes.append(content)
                    footvalue = next_footnote
                    next_footnote += 1
                else:
                    footvalue = content_footnote_map[content]
                query_text += f' <super>{footvalue}</super>'
            story.append(Paragraph(query_text, scenario_style))

            # Scenarios as bullets (no 'start', only 'bulletType')
            if source.get("scenarios"):
                bullet_items = []
                for sc in source["scenarios"]:
                    reason = sc.get("reasoning", "")
                    scen = sc.get("scenario", "")
                    scenario_paragraph = Paragraph(scen, bold_style)
                    if reason:
                        reason_paragraph = Paragraph(reason, scenario_style)
                        # sub bullet as hollow circle
                        bullet_items.append(ListItem([
                            scenario_paragraph,
                            ListFlowable(
                                [ListItem(reason_paragraph)],
                                bulletType='bullet',
                                bulletChar=u"\u25CB",
                                leftIndent=18
                            )
                        ]))
                    else:
                        bullet_items.append(ListItem(scenario_paragraph))
                story.append(ListFlowable(bullet_items, bulletType='bullet'))  # disc bullet for top-level bullets
            story.append(Spacer(1, 12))
        story.append(PageBreak())

    # FOOTNOTES SECTION
    story.append(Spacer(1, 16))
    story.append(Paragraph('Source Content', header_style))
    story.append(Spacer(1, 8))
    for i, ct in enumerate(footnotes, 1):
        story.append(Paragraph(f"{i}. {ct}", scenario_style))
        story.append(Spacer(1, 6))

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
    print(f"Received list of {len(results)} risk analysis results")
    # print("*********")
    # print(results)
    # print("*********")

    return results