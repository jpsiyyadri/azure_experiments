# Register this blueprint by adding the following line of code
# to your entry point file.
# openai_blueprint.register_functions(blueprint)
#
# Please refer to https://aka.ms/azure-functions-python-blueprints


import json
import logging

import azure.functions as func
from langchain import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI

openai_blueprint = func.Blueprint()

with open("config.json", "r") as config_json:
    config = json.load(config_json)


llm = AzureChatOpenAI(
    azure_endpoint=config["openai_api_base"],
    openai_api_version=config["openai_api_version"],
    deployment_name=config["deployment_name"],
    openai_api_key=config["openai_azure_api_key"],
    openai_api_type=config["openai_api_type"],
    model_kwargs={"response_format": {"type": "json_object"}},
)
llm1 = AzureChatOpenAI(
    azure_endpoint=config["openai_api_base"],
    openai_api_version=config["openai_api_version"],
    deployment_name=config["deployment_name"],
    openai_api_key=config["openai_azure_api_key"],
    openai_api_type=config["openai_api_type"],
    request_timeout=650,
)

sample_output_json = {
    "Section 1 - General Information": {
        "Document Identification Information": {
            "Document Name": "text",
            "Document Reference Number": "text",
            "Additional Reference Number": "text",
        },
        "Entity Information": {
            "Entity Name and Address": "textarea",
            "Secondary Entity Name and Address": "textarea",
        },
        "Additional Organisation Information": {
            "Functional Area": "text",
            "Cost Centre": "text",
            "Recipient Location(s)": "textarea",
            "Project Manager": {"Name": "text", "Email": "email", "Phone": "tel"},
            "Clarity ID (optional)": "text",
            "Work Order Number (optional)": "text",
        },
        "Additional Supplier Information": {
            "Supplier Manager": {"Name": "text", "Email": "email", "Phone": "tel"},
            "Supplier Delivery Location(s)": "textarea",
        },
    },
    "Section 2 - Development and Customisation": {
        "Development and Customisation Details": {
            "Is Development or Customisation Required": {
                "type": "radio",
                "options": ["Yes", "No"],
            },
            "Project Start Date": "date",
            "Will Intellectual Property Rights be Owned by the Entity": {
                "type": "radio",
                "options": ["Yes", "No"],
            },
            "Development Specification": "textarea",
            "Development Timetable and Charges": [
                {
                    "Milestone": "text",
                    "Completion Date": "date",
                    "Basis for Charges": "text",
                    "Charges (excludes VAT, Sales Tax and GST)": "number",
                }
            ],
        }
    },
    "Section 3 - Testing": {
        "Testing Details": {
            "Will the Product be Provided and Tested": {
                "type": "radio",
                "options": ["Yes", "No"],
            },
            "Who Will Test the Product": {
                "type": "radio",
                "options": ["Entity", "Supplier"],
            },
            "Deadline for Acceptance": "date",
            "Acceptance Tests": "textarea",
        }
    },
    "Section 4 - Delivery, Warranty, and Licensing": {
        "Delivery Details": {
            "Will the Product be Provided": {"type": "radio", "options": ["Yes", "No"]},
            "Term of License": {"Starts": "date", "Duration": "number"},
            "Scope of Use": "textarea",
            "Warranty Period": "number",
            "Will the Source Code be Provided": {
                "type": "radio",
                "options": ["Yes", "No"],
            },
            "Will the Source Code be Placed into Escrow": {
                "type": "radio",
                "options": ["Yes", "No"],
            },
            "Language for User Interface and Documentation": "text",
            "Product Specification": "textarea",
            "Installation and Data Migration": {
                "type": "radio",
                "options": ["Yes", "No"],
            },
            "Charges for Product": {
                "Trigger for Invoicing": "text",
                "Charges (excludes VAT, Sales Tax and GST)": "number",
            },
        }
    },
    "Section 5 - Goods, including Hardware": {
        "Goods Details": {
            "Will Goods be Provided": {"type": "radio", "options": ["Yes", "No"]},
            "Delivery Address(es) for the Goods": "textarea",
            "Delivery Date(s) and Time(s) for Delivery": "datetime-local",
            "Manufacturer’s Warranty": "textarea",
            "Goods Specification": "textarea",
            "Will the Supplier Install the Goods": {
                "type": "radio",
                "options": ["Yes", "No"],
            },
            "Charges for Goods": {
                "Trigger for Invoicing": "text",
                "Charges (excludes VAT, Sales Tax and GST)": "number",
            },
        }
    },
    "Section 6 - Maintenance and Support": {
        "Maintenance and Support Services": {
            "Will Maintenance and Support be Provided": {
                "type": "radio",
                "options": ["Yes for Product", "Yes for Goods", "No"],
            },
            "Name of Product or Goods Subject to Maintenance and Support": "text",
            "Term of Maintenance and Support Services": {
                "Starts": "date",
                "Duration": "number",
            },
            "When Will Support be Provided": {"Support Hours": "textarea"},
            "Charges for Maintenance and Support": {
                "Trigger for Invoicing": "text",
                "Charges (excludes VAT, Sales Tax and GST)": "number",
            },
            "Details of the Maintenance and Support Services": "textarea",
            "Service Levels": [
                {
                    "Type of Fault": "text",
                    "Response Time During Support Hours": "number",
                    "Repair Time During Support Hours": "number",
                    "Response Time Out of Support Hours": "number",
                    "Repair Time Out of Support Hours": "number",
                }
            ],
        }
    },
    "Section 7 - Other Project Services": {
        "Project Services Details": {
            "Are Project Services Required": {
                "type": "radio",
                "options": ["Yes", "No"],
            },
            "Project Start Date / Effective Date": "date",
            "Project Completion Date / Expiration Date": "date",
            "Project Charging": {
                "Type": {
                    "type": "radio",
                    "options": [
                        "Time and Materials Only (Ordinary mandate)",
                        "Fixed Price Only (Outcome based)",
                        "Both Fixed Price and Time and Materials",
                    ],
                }
            },
            "Project Scope and Requirements": "textarea",
            "Team Composition": [
                {
                    "Role": "text",
                    "Agreed Rate Card $/day": "number",
                    "Revised Rate $ for 2024": "number",
                    "FTE": "number",
                    "Total $ Value": "number",
                }
            ],
            "Support Needed": "textarea",
            "Assumptions": "textarea",
            "Out of Scope Activities": "textarea",
            "Project Timetable and Charges": [
                {
                    "Phase": "text",
                    "Deliverables": "text",
                    "Completion Date": "date",
                    "Basis": "text",
                    "Charges (excludes VAT, Sales Tax and GST)": "number",
                }
            ],
            "Project Deliverables": [
                {
                    "Deliverable ID": "text",
                    "Brief Description": "text",
                    "Delivery Date": "date",
                    "Additional Acceptance Criteria": {
                        "type": "radio",
                        "options": ["Yes", "No"],
                    },
                }
            ],
            "Criteria for the Deliverables": "textarea",
            "Project Team": [
                {"Role": "text", "Named Resource": "text", "Location": "textarea"}
            ],
        }
    },
    "Section 8 - Other": {
        "Approved Subcontractors": [
            {"Role": "text", "Name, Location and Contact Information": "textarea"}
        ],
        "Time and Materials Rate Card": [
            {
                "Role": "text",
                "Location": "text",
                "Hourly / Daily Rate (excludes VAT, Sales Tax and GST)": "number",
            }
        ],
        "Additional Charging Information": {
            "Invoicing and Settlement Currency": "text",
            "Exchange Rate": "text",
        },
        "Additional Security and Compliance Requirements": {
            "Details of Additional Security Measures": "textarea",
            "Additional Compliance Obligations": "textarea",
        },
        "Data Privacy": {
            "Nature and Purpose of Any Processing": "textarea",
            "Types of Personal Data Processed": "textarea",
            "Categories of Individuals Whose Personal Data is Processed": "textarea",
            "Measures Taken to Permit a Restricted International Transfer of Personal Data": "textarea",
        },
        "Quality Management": {
            "Will the Supplier be Required to Comply with Annex B (Quality Management)": {
                "type": "radio",
                "options": ["Yes", "No"],
            }
        },
        "Special Terms": {
            "These Special Terms Will Override the Provisions in the Terms": "textarea"
        },
    },
    "Signatures": {
        "Primary Entity": [
            {
                "Signature": "text",
                "Name": "text",
                "Title": "text",
                "Legal Entity": "text",
                "Date": "date",
            }
        ],
        "Secondary Entity": [
            {
                "Signature": "text",
                "Name": "text",
                "Title": "text",
                "Legal Entity": "text",
                "Date": "date",
            }
        ],
    },
}
api_template = """
Prompt:
Please analyze the provided document and extract the necessary inputs required to recreate a similar document. Structure the extracted inputs in JSON format, including the type of input field required for each (e.g., text field, textarea, date field, number field, radio button, checkbox). Additionally, for radio buttons and checkboxes, provide the possible options.
The JSON should be organized according to the sections and parts of the document, ensuring each part has clearly defined fields and subfields as per the original document's structure. Just give me the json output, nothing else.

Example JSON Output:
json
{sample_output_json}

Document Text:
{pdf_text}
""".strip()
prompt = PromptTemplate(
    input_variables=["pdf_text", "sample_output_json"], template=api_template
)
chain = LLMChain(llm=llm, prompt=prompt)

api_template1 = """
Prompt
Analyze the original document below for changes and generate a new document with the updates. Ensure that the new document maintains the exact formatting, structure, and organization as the original document.

### Original Document
{original_text} 

### Changes
{changed_json}

### Updated Document
Generate the updated document with the changes applied while preserving the formatting with tables and checkboxes, structure, and organization of the original document. generate only document with out any code elements. give only new updated document
""".strip()
prompt = PromptTemplate(
    input_variables=["original_text", "changed_json"], template=api_template1
)
chain1 = LLMChain(llm=llm1, prompt=prompt)


def get_json(text):
    response = chain.run(
        pdf_text=text, sample_output_json=json.dumps(sample_output_json, indent=4)
    )
    return response


def recreated_text(original_text, changed_json):
    response = chain1.run(
        original_text=original_text, changed_json=json.dumps(changed_json, indent=4)
    )
    return response


@openai_blueprint.queue_trigger(
    arg_name="startSOWExtractionQueue",
    queue_name="sow-extraction-queue",
    connection="AzureWebJobsStorage",
)
@openai_blueprint.cosmos_db_output(
    arg_name="opBatchDocument",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="batch",
    # partition_key="{batchid}"
)
@openai_blueprint.cosmos_db_input(
    arg_name="ipFilesDocuments",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="files",
    sql_query="SELECT * FROM c",
    # partition_key="{batchid}"
)
@openai_blueprint.cosmos_db_output(
    arg_name="opFilesDocument",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="files",
    # partition_key="{batchid}"
)
def sow_extraction(
    startSOWExtractionQueue: func.QueueMessage,
    opBatchDocument: func.Out[func.Document],
    ipFilesDocuments: func.DocumentList,
    opFilesDocument: func.Out[func.Document],
) -> None:
    try:
        received_message = json.loads(
            startSOWExtractionQueue.get_body().decode("utf-8")
        )

        # batchid = received_message["batchid"]
        batch_row_id = received_message["batch_row_id"]
        file_row_id = received_message["file_row_id"]

        # fetch extracted text from ipFilesDocuments matching file_row_id
        files_list = [dict(file) for file in ipFilesDocuments]
        if len(files_list) == 0:
            return
        file = [file for file in files_list if file["id"] == file_row_id][0]
        extracted_text = file["extracted_text"]

        # extract SOW from extracted_text
        sow = get_json(extracted_text)

        # update sow_extraction_status, extracted_sow in opFilesDocument
        file["sow_extraction_status"] = "completed"
        file["extracted_sow"] = sow
        opFilesDocument.set(func.Document.from_dict(file))

        # update sow_extraction_status in opBatchDocument
        batches_list = [dict(batch) for batch in ipFilesDocuments]
        if len(batches_list) == 0:
            return
        batch = [batch for batch in batches_list if batch["id"] == batch_row_id][0]
        batch["sow_extraction_status"] = "completed"
        opBatchDocument.set(func.Document.from_dict(batch))
    except Exception as e:
        logging.error(str(e))


@openai_blueprint.route("batch/{batchid}/file/{fileid}/mapping", methods=["POST"])
@openai_blueprint.queue_output(
    arg_name="startSOWGenerationQueue",
    queue_name="sow-generation-queue",
    connection="AzureWebJobsStorage",
)
@openai_blueprint.cosmos_db_input(
    arg_name="ipMappingsDocuments",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="mappings",
    sql_query="SELECT * FROM c",
)
@openai_blueprint.cosmos_db_output(
    arg_name="opMappingsDocument",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="mappings",
)
@openai_blueprint.cosmos_db_input(
    arg_name="ipFilesDocuments",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="files",
    sql_query="SELECT * FROM c",
)
def submit_mapping(
    req: func.HttpRequest,
    startSOWGenerationQueue: func.Out[str],
    opMappingsDocument: func.Out[func.Document],
    ipMappingsDocuments: func.DocumentList,
    ipFilesDocuments: func.DocumentList,
) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        mapped_json = req_body["mapped_json"]
        fileid = req.route_params["fileid"]

        # check if fileid exists in ipFilesDocuments
        files_list = [dict(file) for file in ipFilesDocuments]
        if len(files_list) == 0 or fileid not in [file["id"] for file in files_list]:
            return func.HttpResponse(
                json.dumps({"message": "No files found"}), status_code=404
            )
        
        # get extracted_text from ipFilesDocuments matching fileid
        file = [file for file in files_list if file["id"] == fileid]

        if len(file) == 0:
            return func.HttpResponse(
                json.dumps({"message": "No files found"}), status_code=404
            )

        extracted_text = file[0]["extracted_text"]

        new_mapping_id = str(len(ipMappingsDocuments) + 1)
        new_mapping = {
            "id": new_mapping_id,
            "mapped_json": mapped_json,
            "new_sow_generation": "pending",
            "sow_generation_message": "",
            "sow_generation_start_time": "",
            "sow_generation_end_time": "",
            "fileid": fileid,
            "extracted_text": extracted_text,
        }
        opMappingsDocument.set(func.Document.from_dict(new_mapping))

        # add message to queue
        startSOWGenerationQueue.set(
            json.dumps({"mapping_id": new_mapping_id})
        )

        return func.HttpResponse(
            json.dumps({"data": new_mapping, "message": "success"}),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as e:
        return func.HttpResponse(str(e), status_code=500)


@openai_blueprint.queue_trigger(
    arg_name="startSOWGenerationQueue",
    queue_name="sow-generation-queue",
    connection="AzureWebJobsStorage",
)
@openai_blueprint.cosmos_db_input(
    arg_name="ipMappingsDocuments",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="mappings",
    sql_query="SELECT * FROM c",
)
@openai_blueprint.cosmos_db_output(
    arg_name="opMappingsDocument",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="mappings",
    # partition_key="{batchid}"
)
def sow_generation(
    startSOWGenerationQueue: func.QueueMessage,
    ipMappingsDocuments: func.DocumentList,
    opMappingsDocument: func.Out[func.Document],
) -> None:
    try:
        received_message = json.loads(
            startSOWGenerationQueue.get_body().decode("utf-8")
        )

        mapping_id = received_message["mapping_id"]
        # get the mappings from ipMappingsDocuments matching fileid
        mappings_list = [dict(mapping) for mapping in ipMappingsDocuments]

        filtered_mappings = [
            mapping for mapping in mappings_list if mapping["id"] == mapping_id
        ]

        if len(filtered_mappings) == 0:
            raise Exception("No mappings found")

        mapping = filtered_mappings[0]
        mapped_json = mapping["mapped_json"]
        extracted_text = mapping["extracted_text"]

        mapping["new_sow_generation"] = "processing"
        opMappingsDocument.set(func.Document.from_dict(mapping))


        # generate new sow
        new_sow = recreated_text(extracted_text, mapped_json)

        # update new_sow_generation, sow_generation_message, sow_generation_start_time, sow_generation_end_time in mapping
        mapping["new_sow_generation"] = "completed"
        mapping["sow_generation_message"] = "success"
        mapping["sow_generation_start_time"] = ""
        mapping["sow_generation_end_time"] = ""
        mapping["new_sow"] = new_sow

        # update mapping in opMappingsDocument
        opMappingsDocument.set(func.Document.from_dict(mapping))

    except Exception as e:
        logging.error(str(e))


@openai_blueprint.route(
    "batch/{batchid}/file/{fileid}/mapping/{mapping_id}", methods=["GET"]
)
@openai_blueprint.cosmos_db_input(
    arg_name="ipMappingsDocuments",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="mappings",
    sql_query="SELECT * FROM c where c.id = {mapping_id}",
)
def get_one_mapping(
    req: func.HttpRequest,
    ipMappingsDocuments: func.DocumentList,
) -> func.HttpResponse:
    try:
        mapping_id = req.route_params["mapping_id"]

        # fetch mappings from ipMappingsDocuments matching mapping_id
        mappings_list = [dict(mapping) for mapping in ipMappingsDocuments]

        if len(mappings_list) == 0:
            return func.HttpResponse(
                json.dumps({"message": "No mappings found"}), status_code=404
            )

        mappings = [mapping for mapping in mappings_list if mapping["id"] == mapping_id]

        return func.HttpResponse(
            json.dumps({"data": mappings, "message": "success"}),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as e:
        return func.HttpResponse(str(e), status_code=500)


# get all mappings for a file
@openai_blueprint.route("batch/{batchid}/file/{fileid}/mapping/all", methods=["GET"])
@openai_blueprint.cosmos_db_input(
    arg_name="ipMappingsDocuments",
    connection="AzureWebJobsCosmosDBConnectionString",
    database_name="books",
    container_name="mappings",
    sql_query="SELECT * FROM c where c.fileid = {fileid}",
)
def get_all_mappings(
    req: func.HttpRequest,
    ipMappingsDocuments: func.DocumentList,
) -> func.HttpResponse:
    try:
        fileid = req.route_params["fileid"]

        # fetch mappings from ipMappingsDocuments matching fileid
        mappings_list = [dict(mapping) for mapping in ipMappingsDocuments]

        if len(mappings_list) == 0:
            return func.HttpResponse(
                json.dumps({"message": "No mappings found"}), status_code=404
            )

        mappings = [mapping for mapping in mappings_list if mapping["fileid"] == fileid]

        return func.HttpResponse(
            json.dumps({"data": mappings, "message": "success"}),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as e:
        return func.HttpResponse(str(e), status_code=500)
