import json
import logging

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


sample_response = {
    "Part A - Parties": {
        "SOW Identification Information": {
            "SOW Name": "text",
            "Novartis Contract Reference Number": "text",
            "Supplier Contract Reference Number": "text",
        },
        "Legal Entity Information": {
            "Novartis Service Recipient Legal Entity Name and Address": "textarea",
            "Supplier Legal Entity Name and Address": "textarea",
        },
        "Additional Novartis Organisation Information": {
            "IT Functional Area": "text",
            "Cost Centre": "text",
            "Service Recipient Location(s)": "textarea",
            "Novartis Project Manager": {
                "Name": "text",
                "Email": "email",
                "Phone": "tel",
            },
            "Clarity ID (optional)": "text",
            "Work Order Number (optional)": "text",
        },
        "Additional Supplier Organisation Information": {
            "Supplier Project Manager": {
                "Name": "text",
                "Email": "email",
                "Phone": "tel",
            },
            "Supplier Delivery Location(s)": "textarea",
        },
    },
    "Part B - Development and Customisation of Software": {
        "Development and Customisation": {
            "Is Development or Customisation of Software Required": {
                "type": "radio",
                "options": ["Yes", "No"],
            },
            "Project Start Date": "date",
            "Will Novartis Own the Intellectual Property Rights in the Developed Works": {
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
    "Part C - Software Testing": {
        "Software Testing": {
            "Will Software be Provided and Tested": {
                "type": "radio",
                "options": ["Yes", "No"],
            },
            "Who Will Test the Software": {
                "type": "radio",
                "options": ["Novartis", "Supplier"],
            },
            "Deadline for Acceptance": "date",
            "Acceptance Tests": "textarea",
        }
    },
    "Part D - Software Delivery, Warranty, and Licensing": {
        "Software Delivery": {
            "Will Software be Provided": {"type": "radio", "options": ["Yes", "No"]},
            "Term of License": {"Starts": "date", "Duration": "number"},
            "Scope of Use": "textarea",
            "Warranty Period": "number",
            "Will the Source Code for the Software be Provided to Novartis": {
                "type": "radio",
                "options": ["Yes", "No"],
            },
            "Will the Source Code for the Software be Placed into Escrow": {
                "type": "radio",
                "options": ["Yes", "No"],
            },
            "Language for the User Interface and User Documentation": "text",
            "Software Specification": "textarea",
            "Software Installation and Data Migration": {
                "type": "radio",
                "options": ["Yes", "No"],
            },
            "Charges for Software": {
                "Trigger for Invoicing": "text",
                "Charges (excludes VAT, Sales Tax and GST)": "number",
            },
        }
    },
    "Part E - Goods, including Hardware": {
        "Goods": {
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
    "Part F - Maintenance and Support": {
        "Maintenance and Support Services": {
            "Will Maintenance and Support be Provided": {
                "type": "radio",
                "options": ["Yes for Software", "Yes for Goods", "No"],
            },
            "Name of Software or Goods Subject to Maintenance and Support": "text",
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
    "Part G - Other Project Services": {
        "Project Services": {
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
    "Part H - Other": {
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
        "Novartis": [
            {
                "Signature": "text",
                "Name": "text",
                "Title": "text",
                "Legal Entity": "text",
                "Date": "date",
            }
        ],
        "Supplier": [
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


@app.route(
    route="batch/{batchid}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS
)
def get_batch(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(
            {
                "status": "progress",
                "text_extraction_status": "progress",
                "text_extraction_message": "",
                "sow_extraction_status": "pending",
                "sow_extraction_message": "",
            }
        ),
        status_code=200,
    )


@app.route(
    route="batch/{batchid}/sow/submit",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def submit_sow(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"message": "SOW submitted succesfully!"}), status_code=200
    )


@app.route(
    route="batch/{batchid}/sow/{sow_id}/template",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def get_template(req: func.HttpRequest) -> func.HttpResponse:
    # return extracted template
    return func.HttpResponse(
        json.dumps(
            {
                "sow_template": {
                    "sow_id": "1",
                    "batchid": "123",
                    "section": sample_response,
                }
            }
        ),
        status_code=200,
    )


@app.route(
    route="batch/{batchid}/sow/{sow_id}/mapping/{mapping_id}",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def get_mapping(req: func.HttpRequest) -> func.HttpResponse:
    # return submitted mapping
    return func.HttpResponse(
        json.dumps(
            {
                "mapping": {
                    "mapping_id": "1",
                    "sow_id": "1",
                    "batchid": "123",
                    "section": sample_response,
                }
            }
        ),
        status_code=200,
    )


@app.route(
    route="batch/{batchid}/sow/all",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def get_all_sows(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(
            {
                "sow_templates": [
                    {"sow_id": "1", "batchid": "123", "template": sample_response}
                ]
            }
        ),
        status_code=200,
    )


@app.route(
    route="batch/{batchid}/sow/{sow_id}/mapping/all",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def get_all_mappings(req: func.HttpRequest) -> func.HttpResponse:
    # return submitted mapping
    return func.HttpResponse(
        json.dumps(
            {
                "mappings": [
                    {
                        "mapping_id": "1",
                        "sow_id": "1",
                        "batchid": "123",
                        "section": sample_response,
                    }
                ]
            }
        ),
        status_code=200,
    )


@app.route(
    route="batch/generate_id", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS
)
def generate_id(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(json.dumps({"batchid": "123"}), status_code=200)


@app.route(
    route="batch/{batchid}/create/file/{filename}",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def create_batch(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"message": "File uploaded succesfully!"}), status_code=200
    )
