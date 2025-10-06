#celery -A celery_config worker --loglevel=debug

#for docker file need to include, for plotly image
# brew install cairo pango gdk-pixbuf libffi

from dotenv import load_dotenv
load_dotenv()

from flask import render_template_string

from io import BytesIO, StringIO
import os
import re
import pandas as pd
import json
import textwrap
from pycomponents.graph import quant_scenario_app
from celery_config import celery_app
import plotly.graph_objects as go
import base64

import traceback

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfgen import canvas

import weasyprint

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


def plot_histogram_base64(samples):
    fig = go.Figure(data=[
        go.Histogram(
            x=samples,
            marker_color="#2B303a"  # set the bar color here
        )
    ])
    fig.update_layout(
        title="Outcome Distribution",
        title_x=0.5,
        xaxis_title="Outcome",
        yaxis_title="Frequency",
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="#eaeaeb", 
    )
    img_bytes = fig.to_image(format="png", width=600, height=350)
    encoded = base64.b64encode(img_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}"



def generate_simulation_pdf(data):
    tailwind_css = """
    .card { background: white; border-radius: 12px; padding: 0 20px; margin: 20px auto; width: 95%; font-family: Arial, sans-serif; }
    .card h3 { margin-bottom: 10px; font-size: 1.2rem; }
    .border { border: 1px solid #ddd; }
    .mb-4 { margin-bottom: 1rem; }
    """

    cards_html = ""
    for idx, scenario in enumerate(data):
        scenario["histogram_base64"] = plot_histogram_base64(scenario["samples"])
        page_break = "page-break-before: always;" if idx > 0 else ""
        cards_html += render_template_string("""
        <div class="card border mb-4" style="{{ page_break }}">
            <h3>RISK: {{ scenario.risk }}</h3>
            <div style="margin-bottom: 8px;"><strong>Scenario:</strong><br> {{ scenario.scenario }}</div>
            <hr>
            {% if scenario.formula %}
                <div style="margin-top: 8px;">
                    <strong>Formula:</strong><br>
                    {{ scenario.formula_equals }} = {{ scenario.formula }}<br>
                </div>
            {% endif %}
            <div style="margin-top: 8px;">
                <hr>
                <div style="display: flex; flex-wrap: wrap; gap: 12px;">
                    {% for v in scenario.variables %}
                        <div style="
                            width: 48%;
                            box-sizing: border-box;
                            border: 1px solid #2b303a;
                            border-radius: 6px;
                            padding: 8px;
                            background: #eaeaeb;
                        ">
                            <div style="font-weight: bold; margin-bottom: 4px; overflow-wrap: anywhere;">
                                {{ v.name }}
                            </div>

                            <div style="margin-bottom: 8px;">
                                Distribution: {{ v.distribution }}
                            </div>
                            <ul style="margin-top: 4px; margin-bottom: 0; padding-left: 18px;">
                                {% for param, val in v.parameters.items() %}
                                    <li>{{ param }}: {{ val }}</li>
                                {% endfor %}
                            </ul>
                        </div>
                    {% endfor %}
                </div>
                <hr>
            </div>
            <div>
                Mean: <b>${{ scenario.summary.mean | round(2) }}</b><br>
                5th percentile: <b>${{ scenario.summary.percentile_5 | round(2) }}</b><br>
                95th percentile: <b>${{ scenario.summary.percentile_95 | round(2) }}</b><br>
            </div>
            {% if scenario.histogram_base64 %}
                <div style="margin-top: 10px; margin-bottom: 5px;">
                    <img src="{{ scenario.histogram_base64 }}" style="width:95%; padding-top:10px; border:1px solid #2b303a; border-radius:6px;">
                    <div style="font-size:0.95em; text-align:center; padding-top:20px; text-align:center; opacity:0.8;">Outcome Distribution</div>
                </div>
            {% endif %}
        </div>
        """, scenario=scenario, page_break=page_break)

    html = f"<html><head><style>{tailwind_css}</style></head><body>{cards_html}</body></html>"

    pdf_buffer = BytesIO()
    weasyprint.HTML(string=html).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer



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