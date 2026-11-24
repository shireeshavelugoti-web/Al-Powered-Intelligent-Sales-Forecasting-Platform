import os
import json

from google import genai
from dotenv import load_dotenv


load_dotenv()


def get_gemini_api_key():
    """Accept both the app's legacy name and Google's standard env var."""
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def generate_ai_response(prompt):

    api_key = get_gemini_api_key()

    if not api_key:
        raise RuntimeError("Gemini API key is missing")

    client = genai.Client(api_key=api_key)

    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-2.5-flash"
    )

    response = client.models.generate_content(
        model=model,
        contents=prompt
    )

    raw = (response.text or "").strip()

    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    return json.loads(raw)


def generate_email(lead, service, tone, context=None):

    prompt = f"""
    You are a professional B2B sales email writer.

    Generate a personalized sales email.

    COMPANY INFORMATION:

    Company: {lead['company_name']}
    Industry: {lead['industry']}
    Contact: {lead['contact_person']}
    Website: {lead['website']}
    Technology: {lead['technology_stack']}
    Description: {lead['description']}

    OUR SERVICES:
    {service}

    ADDITIONAL CONTEXT:
    {context or "None"}

    EMAIL TONE:
    {tone}

    REQUIREMENTS:

    1. Generate a professional email.
    2. Personalize it based on the company.
    3. Explain how our services may help.
    4. Include a suitable call to action.
    5. Keep it concise.
    6. Do not invent company facts.
    7. Do not claim an unverified business requirement.

    Return ONLY JSON:

    {{
        "subject": "Email subject",
        "body": "Complete email body"
    }}
    """

    result = generate_ai_response(prompt)

    if not result.get("subject") or not result.get("body"):
        raise ValueError("Invalid email response from AI")

    return result


def generate_recommendation(
    lead,
    score,
    priority
):

    prompt = f"""
    You are an AI sales strategy assistant.

    Analyse this prospect and generate an outreach strategy.

    COMPANY:
    {lead['company_name']}

    INDUSTRY:
    {lead['industry']}

    BUSINESS DESCRIPTION:
    {lead['description']}

    LEAD SCORE:
    {score}/100

    PRIORITY:
    {priority}

    Generate:

    1. Communication channel.
    2. Suggested follow-up timing.
    3. Outreach strategy.
    4. Next recommended action.

    Do not invent previous interactions or contact history.

    Return ONLY JSON:

    {{
        "channel": "Email",
        "follow_up_timing": "Within 48 hours",
        "strategy": "Recommended strategy",
        "next_action": "Recommended next action"
    }}
    """

    result = generate_ai_response(prompt)

    required = [
        "channel",
        "follow_up_timing",
        "strategy",
        "next_action"
    ]

    if any(not result.get(key) for key in required):
        raise ValueError("Invalid recommendation response")

    return result


def analyze_company(lead):

    prompt = f"""
    You are a B2B company intelligence analyst.

    Analyse the following company using only the supplied information.

    COMPANY:
    Company name: {lead.get('company_name', 'Not provided')}
    Industry: {lead.get('industry', 'Not provided')}
    Contact: {lead.get('contact_person', 'Not provided')}
    Website: {lead.get('website', 'Not provided')}
    Employee count: {lead.get('employee_count', 'Not provided')}
    Location: {lead.get('location', 'Not provided')}
    Description: {lead.get('description', 'Not provided')}
    Technology: {lead.get('technology_stack', 'Not provided')}

    Generate:

    1. A concise company overview.
    2. A list of likely business needs.
    3. A list of sales opportunities.
    4. A concise industry analysis.
    5. A qualification score from 0 to 100.
    6. A specific recommended next action.

    Do not invent facts that are not supported by the supplied information.

    Return ONLY JSON:

    {{
        "company_overview": "Company overview",
        "business_needs": ["Business need"],
        "opportunities": ["Sales opportunity"],
        "industry_analysis": "Industry analysis",
        "qualification_score": 75,
        "recommended_action": "Recommended action"
    }}
    """

    result = generate_ai_response(prompt)

    required_strings = [
        "company_overview",
        "industry_analysis",
        "recommended_action"
    ]

    if any(not isinstance(result.get(key), str) or not result[key].strip()
           for key in required_strings):
        raise ValueError("Invalid company overview response")

    for key in ["business_needs", "opportunities"]:
        value = result.get(key)
        if (not isinstance(value, list) or
                not value or
                any(not isinstance(item, str) or not item.strip()
                    for item in value)):
            raise ValueError("Invalid company analysis lists")

    score = result.get("qualification_score")
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise ValueError("Invalid qualification score")

    score = int(score)
    if not 0 <= score <= 100:
        raise ValueError("Qualification score must be between 0 and 100")

    result["qualification_score"] = score
    return result
