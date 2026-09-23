import os
import json

from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set")

client = genai.Client(api_key=api_key)


def analyze_document(text: str):

    prompt = f"""
You are a document analysis system.

Analyze the following document and return ONLY valid JSON.

The JSON must contain exactly these fields:

{{
    "document_type": "The type of document, such as invoice, resume, contract, certificate, letter, report, receipt, or unknown",
    "summary": "A concise summary of the document",
    "topics": ["topic 1", "topic 2"],
    "people": ["person 1", "person 2"],
    "organizations": ["organization 1", "organization 2"],
    "dates": ["date 1", "date 2"]
}}

Rules:

- Return valid JSON only.
- Do not use markdown.
- Do not add explanations outside the JSON.
- If information is not present, return an empty array.
- Do not invent information.
- document_type must be a short lowercase category.
- If you cannot determine the type, use "unknown".

DOCUMENT:

{text}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        result = response.text
        parsed_result = json.loads(result)
        return json.dumps(parsed_result)

    except Exception as e:
        print(f"AI analysis failed: {e}")
        raise RuntimeError(
            "Document analysis service is temporarily unavailable."
        )


def generate_answer(prompt: str):

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:

        print(f"AI answer generation failed: {e}")

        raise RuntimeError(
            "Answer generation service is temporarily unavailable."
        )