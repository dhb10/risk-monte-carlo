from dotenv import load_dotenv
load_dotenv(override=True)

import os
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import zipfile
import json
from pycomponents.simulation import run_simulation
from azure.storage.blob import BlobServiceClient
import numpy as np
import pandas as pd
import io

from celery_config import celery_app
from celery import chord

from tasks import df_to_list_of_risk_dicts, generate_scenarios, chord_callback, generate_risk_scenarios_pdf

###---ENV VARIABLES---###
azure_openai_api_key = os.getenv("AZUREOPENAI_API_KEY")
azure_openai_endpoint = os.getenv("AZUREOPENAI_ENDPOINT")
azure_openai_embedding_endpoint = os.getenv("AZUREOPENAI_EMBEDDING_ENDPOINT")
tavily_api_key = os.getenv("TAVILY_API_KEY")

blob_connection_string = os.getenv("BLOB_CONNECTION_STRING")
blob_container_name = os.getenv("BLOB_CONTAINER_RISKID")
blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
container_client = blob_service_client.get_container_client(blob_container_name)
blob_container_key=os.getenv("BLOB_CONTAINER_KEY")


###---FLASK INIT---###
# app = Flask(__name__,static_folder='dist')
# CORS(app, resources={r"/*": {"origins": "https://risk-definition-assistant-a9dshthcfqemfue8.centralus-01.azurewebsites.net"}})

# #for dev
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})



###---MAIN---###


@app.route('/generate_csv', methods=['POST', 'OPTIONS'])
def generate_csv():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight successful'})
        response.headers.update({
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Credentials": "true",
        })
        return response, 200

    payload = request.json
    print('INCOMING PAYLOAD:', repr(payload))  # DEBUG
    if not payload or 'data' not in payload:
        return jsonify({"error": "No data provided"}), 400

    records = []
    for risk_bundle in payload["data"]:
        risk_name = risk_bundle.get("risk_name", "")
        risk_definition = risk_bundle.get("risk_definition", "")
        results = risk_bundle.get("results", {})
        scenario_docs = results.get("scenario_documents", [])  # <-- THIS IS THE ARRAY!
        for entry in scenario_docs:
            search_query = entry.get("search_query", "")
            title = entry.get("title", "")
            url = entry.get("url", "")
            scenarios = entry.get("scenarios", [])
            for s in scenarios:
                records.append({
                    "risk_name": risk_name,
                    "risk_definition": risk_definition,
                    "search_query": search_query,
                    "title": title,
                    "url": url,
                    "scenario": s.get("scenario", ""),
                    "reasoning": s.get("reasoning", ""),
                })

    df = pd.DataFrame(records)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    filename = "generated_scenarios.csv"
    return send_file(
        io.BytesIO(csv_buffer.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename,
    )

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight successful'})
        response.headers.update({
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Credentials": "true",
        })
        return response, 200
    
    payload = request.json
    if not payload or 'data' not in payload:
        return jsonify({"error": "No data provided"}), 400
    pdf_buffer = generate_risk_scenarios_pdf(payload['data'])
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='risk_scenarios.pdf'
    )



@app.route("/simulate", methods=['POST', 'OPTIONS'])
def simulate():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight successful'})
        response.headers.update({
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Credentials": "true",
        })
        return response, 200

    if request.method == 'POST':
        # --- Manual Entry (JSON) ---
        if request.content_type.startswith('application/json'):
            data = request.json
            results = run_simulation(
                data["variables"],
                data["formula"],
                data.get("num_trials", 10000)
            )
            summary = {
                "mean": float(np.mean(results)),
                "percentile_5": float(np.percentile(results, 5)),
                "percentile_95": float(np.percentile(results, 95)),
            }
            return jsonify({
                "summary": summary,
                "samples": results.tolist()
            })
        
        #csv upload
        elif request.content_type.startswith('multipart/form-data'):
            if 'file' not in request.files:
                return jsonify({"error": "No file part"}), 400
            file = request.files['file']

            try:
                df = pd.read_csv(file)
                # Normalize columns
                df.columns = [col.strip().lower() for col in df.columns]

                # Group by scenario (and, if needed, 'risk')
                scenario_groups = df.groupby(['risk', 'scenario', 'formula','formula_equals'], dropna=False)

                output = []

                for (risk, scenario, formula, formula_equals), group in scenario_groups:
                    variables = []
                    for _, row in group.iterrows():
                        variable_name = row['variable'] if 'variable' in row else ""
                        distribution = row['distribution'].lower() if 'distribution' in row and pd.notnull(row['distribution']) else ""
                        parameters = {}

                        if distribution in ['normal', 'lognormal']:
                            parameters = {
                                "mean": float(row['mean']),
                                "stddev": float(row.get('std_dev', row.get('stddev', 0))),
                            }
                        elif distribution == 'triangular':
                            parameters = {
                                "min": float(row['min']),
                                "mode": float(row['mode']),
                                "max": float(row['max']),
                            }
                        elif distribution == 'uniform':
                            parameters = {
                                "min": float(row['min']),
                                "max": float(row['max']),
                            }

                        variables.append({
                            "name": variable_name,
                            "distribution": distribution,
                            "parameters": parameters,
                        })

                    # Now run simulation for this scenario (with all its variables and formula)
                    results = run_simulation(variables, formula, 10000)
                    summary = {
                        "mean": float(np.mean(results)),
                        "percentile_5": float(np.percentile(results, 5)),
                        "percentile_95": float(np.percentile(results, 95)),
                    }

                    output.append({
                        "risk": risk,
                        "scenario": scenario,
                        "variables": variables,
                        "formula": formula,
                        "formula_equals": formula_equals,
                        "summary": summary,
                        "samples": results.tolist(),
                    })
                # for i in output:
                #     print(i['scenario'])
                #     print(i['variables'])
                # print(output)
                return jsonify(output)
            except Exception as e:
                return jsonify({"error": f"Failed to process CSV: {str(e)}"}), 400
        else:
            return jsonify({"error": "Unsupported Content-Type"}), 415
    

# @app.route("/download_results_zip", methods=["GET"])
# def download_results_zip():
#     csv_blob_name = "pivoted_df.csv"
#     pptx_blob_name = "risk_summary_combined.pptx"
#     pdf_blob_name = "risk_summary.pdf"  # Add this

#     csv_blob = container_client.get_blob_client(csv_blob_name)
#     pptx_blob = container_client.get_blob_client(pptx_blob_name)
#     pdf_blob = container_client.get_blob_client(pdf_blob_name)  # Add this

#     # download content
#     csv_stream = io.BytesIO()
#     pptx_stream = io.BytesIO()
#     pdf_stream = io.BytesIO()
    
#     csv_blob.download_blob().readinto(csv_stream)
#     pptx_blob.download_blob().readinto(pptx_stream)
#     pdf_blob.download_blob().readinto(pdf_stream)  # Add this

#     # reset file pointers
#     csv_stream.seek(0)
#     pptx_stream.seek(0)
#     pdf_stream.seek(0)  # Add this

#     # in-memory zip
#     zip_buffer = io.BytesIO()
#     with zipfile.ZipFile(zip_buffer, "w") as zip_file:
#         zip_file.writestr("pivoted_df_for_reference.csv", csv_stream.read())
#         zip_file.writestr("risk_summary_combined.pptx", pptx_stream.read())
#         zip_file.writestr("risk_summary.pdf", pdf_stream.read())  # Add this
#     zip_buffer.seek(0)

#     return send_file(
#         zip_buffer,
#         mimetype="application/zip",
#         as_attachment=True,
#         download_name="risk_outputs.zip"
#     )


@app.route('/scenarios', methods=['POST', 'OPTIONS'])
def generate_risk_scenarios():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight successful'})
        response.headers.update({
            # "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Credentials": "true",
        })
        return response, 200

    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                return jsonify({"error": "No file provided."}), 400

            file = request.files['file']

            # Read DataFrame
            try:
                df = pd.read_csv(file)
            except Exception as e:
                return jsonify({"error": f"Error reading CSV file: {str(e)}"}), 500
            
            # Convert to list of dicts (assuming this returns what you want)
            risk_list = df_to_list_of_risk_dicts(df)

            # print(risk_list[1])
            # risk_list = risk_list[1:]

            # If your celery signature expects the full dict:
            scenario_tasks = [generate_scenarios.s(risk) for risk in risk_list]

            # Run the chord
            job = chord(scenario_tasks)(chord_callback.s())
            
            return jsonify({"status": "processing", "task_id": job.id}), 202


        except Exception as e:
            print(f"Error in /scenarios: {e}")
            return jsonify({"error": "An unexpected error occurred. Please try again."}), 500


@app.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    task_result = celery_app.AsyncResult(task_id)
    response = {
        "task_id": task_id,
        "state": task_result.state,
        "result": task_result.result if task_result.state == "SUCCESS" else None
    }


    # with open(os.path.expanduser("~/Desktop/flask_serve_debug.json"), "w", encoding="utf-8") as f:
    #     f.write(json.dumps(response, indent=2, ensure_ascii=False))


    return jsonify(response)


# # #serve react static files - uncomment for build
# @app.route("/", defaults={"path": ""})
# @app.route("/<path:path>")
# def serve_react(path):
#     # If the path exists in the dist directory, serve it
#     if path and os.path.exists(os.path.join(app.static_folder, path)):
#         return send_from_directory(app.static_folder, path)
#     else:
#         # Otherwise, serve the index.html for the root or any other non-static request
#         return send_from_directory(app.static_folder, 'index.html')


# if __name__ == '__main__':
#     app.run(host="0.0.0.0", port=5000, debug=False)

# @app.after_request
# def add_cors_headers(response):
#     response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
#     response.headers['Access-Control-Allow-Credentials'] = 'true'
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
#     response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
#     return response


if __name__ == "__main__":
    app.run(debug=True)

