import json
import os

from dotenv import load_dotenv
from groq import Groq

from app.models.schemas import (
    RFQ,
    VendorQuotation
)


load_dotenv()


GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)


if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is not set in the environment variables."
    )


client = Groq(
    api_key=GROQ_API_KEY
)


def ask_groq(
    prompt: str
) -> str:
    """
    Sends a normal prompt to the Groq API
    and returns the generated text response.
    """

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",

        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant "
                    "for a procurement automation platform."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.2
    )

    generated_text = (
        response.choices[0].message.content
    )

    if not generated_text:
        raise ValueError(
            "No response received from the Groq API."
        )

    return generated_text


def extract_rfq_data(
    rfq_text: str
) -> RFQ:
    """
    Converts unstructured RFQ text
    into a validated RFQ object.
    """

    prompt = f"""
Extract procurement requirements from the RFQ text below.

Return only one valid JSON object.

Required JSON structure:

{{
    "rfq_title": "string",
    "department": "string",
    "currency": "INR",
    "required_delivery_days": 15,
    "required_warranty_months": 36,
    "items": [
        {{
            "item_name": "Laptop",
            "required_quantity": 20,
            "specifications": {{
                "ram": "16 GB",
                "storage": "512 GB SSD",
                "processor": "Intel i7"
            }}
        }}
    ]
}}

Rules:
1. Return only valid JSON.
2. Do not include markdown or explanations.
3. Use "General" if department is missing.
4. Use "INR" if currency is missing.
5. Put item-specific technical details inside specifications.
6. Include only information available in the RFQ.
7. Convert warranty years into months.
8. Use 0 for required_warranty_months if warranty is missing.
9. Do not invent requirements.

RFQ TEXT:
{rfq_text}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",

        messages=[
            {
                "role": "system",
                "content": (
                    "You extract structured procurement data "
                    "from RFQ documents."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        response_format={
            "type": "json_object"
        },

        temperature=0
    )

    generated_text = (
        response.choices[0].message.content
    )

    if not generated_text:
        raise ValueError(
            "No structured RFQ response received."
        )

    rfq_dictionary = json.loads(
        generated_text
    )

    return RFQ.model_validate(
        rfq_dictionary
    )


def extract_vendor_data(
    vendor_text: str
) -> VendorQuotation:
    """
    Converts unstructured vendor quotation text
    into a validated VendorQuotation object.
    """

    prompt = f"""
Extract vendor quotation details from the text below.

Return only one valid JSON object.

Required JSON structure:

{{
    "vendor_name": "string",
    "currency": "INR",
    "delivery_days": 12,
    "warranty_months": 36,
    "payment_terms_days": 30,
    "technical_compliance_percent": 100,
    "past_rating": 0,
    "line_items": [
        {{
            "item_name": "Laptop",
            "quoted_quantity": 20,
            "unit_price": 58000,
            "specifications": {{
                "ram": "16 GB",
                "storage": "512 GB SSD",
                "processor": "Intel i7"
            }}
        }}
    ]
}}

Rules:
1. Return only valid JSON.
2. Do not include markdown or explanations.
3. Use "INR" if currency is missing.
4. Remove commas and currency symbols from prices.
5. Convert warranty years into months.
6. Use 100 for technical_compliance_percent temporarily.
7. Use 0 for past_rating if it is missing.
8. Extract every item-specific technical specification mentioned.
9. Store technical specifications inside that item's specifications object.
10. Use an empty specifications object only when no specifications are mentioned.
11. Include only products actually quoted.
12. Do not invent prices, quantities, specifications, or products.

VENDOR QUOTATION TEXT:
{vendor_text}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",

        messages=[
            {
                "role": "system",
                "content": (
                    "You extract structured procurement data "
                    "from vendor quotation documents."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        response_format={
            "type": "json_object"
        },

        temperature=0
    )

    generated_text = (
        response.choices[0].message.content
    )

    if not generated_text:
        raise ValueError(
            "No structured vendor response received."
        )

    vendor_dictionary = json.loads(
        generated_text
    )

    return VendorQuotation.model_validate(
        vendor_dictionary
    )


if __name__ == "__main__":

    sample_rfq_text = """
    Request For Quotation

    Company: ABC Pvt Ltd

    Requirements:

    Laptop
    Quantity: 20
    RAM: 16 GB
    Storage: 512 GB SSD
    Processor: Intel i7

    Monitor
    Quantity: 20
    Size: 24 Inch

    Delivery Days: 15
    Warranty: 3 Years
    Payment Terms: 30 Days
    """

    structured_rfq = extract_rfq_data(
        sample_rfq_text
    )

    print("Structured RFQ:")

    print(
        structured_rfq.model_dump_json(
            indent=2
        )
    )

    sample_vendor_text = """
    Vendor Quotation

    Vendor Name: Dell Technologies

    Laptop
    Quantity: 20
    Unit Price: 58000
    RAM: 16 GB
    Storage: 512 GB SSD
    Processor: Intel i7

    Monitor
    Quantity: 20
    Unit Price: 9500
    Size: 24 Inch

    Delivery Days: 12
    Warranty: 3 Years
    Payment Terms: 30 Days
    """

    structured_vendor = extract_vendor_data(
        sample_vendor_text
    )

    print("\nStructured Vendor Quotation:")

    print(
        structured_vendor.model_dump_json(
            indent=2
        )
    )


# =========================================================================
# llm_services.py Summary
# =========================================================================

# 1. Loads the Groq API key from the .env file.

# 2. Creates the Groq client.

# 3. ask_groq() sends normal prompts to the LLM.

# 4. extract_rfq_data() converts RFQ text into structured JSON.

# 5. RFQ extraction now includes required warranty months.

# 6. extract_vendor_data() converts vendor text into structured JSON.

# 7. Vendor extraction now includes item-specific specifications.

# 8. json.loads() converts the LLM JSON string into a Python dictionary.

# 9. Pydantic validates the dictionary and creates typed objects.

# 10. The main block tests both RFQ and vendor extraction.

