import json
import os
from typing import Any, Mapping

from google import genai
from dotenv import load_dotenv


load_dotenv()


def get_gemini_api_key() -> str | None:
    """Read either supported Gemini API key environment variable."""
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def fallback_analysis(lead):
    industry = lead.get("industry", "Unknown")
    return {

        "company_overview":
            f"{lead['company_name']} operates in {industry}. "
            "This overview uses the information provided.",

        "business_needs": [
            f"Review operational requirements in the {industry} sector",
            "Identify technology and business improvement opportunities"
        ],

        "opportunities": [
            "Explore business process automation",
            "Evaluate software and cloud optimization opportunities"
        ],

        "industry_analysis":
            f"The company belongs to the {industry} industry. "
            "Further market research is recommended.",

        "qualification_score": 50,

        "recommended_action":
            "Verify business requirements and contact the decision-maker."
    }


def analyze_company(lead):

    api_key = get_gemini_api_key()

    if not api_key:
        return fallback_analysis(lead)

    client = genai.Client(api_key=api_key)

    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-2.5-flash"
    )

    prompt = f"""
    You are an expert B2B sales intelligence assistant.
    Analyse the following company information.
    Company Information:
    {json.dumps(lead)}
    Generate:
    1. Company Overview
    2. Business Needs
    3. Potential Business Opportunities
    4. Industry Analysis
    5. Qualification Score from 0 to 100
    6. Recommended Action

    Do not invent company facts.

    Return ONLY valid JSON in this format:

    {{
        "company_overview": "Description",

        "business_needs": [
            "Need 1",
            "Need 2"
        ],

        "opportunities": [
            "Opportunity 1",
            "Opportunity 2"
        ],

        "industry_analysis": "Industry details",

        "qualification_score": 85,

        "recommended_action": "Recommended action"
    }}
    """
    response = client.models.generate_content(
        model=model,
        contents=prompt
    )

    raw = response.text.strip()
    raw = raw.removeprefix("```json")
    raw = raw.removesuffix("```").strip()
    data = json.loads(raw)

    data["qualification_score"] = max(
        0,
        min(100, int(data["qualification_score"]))
    )

    return data


def _fallback_email_draft(
    lead: Mapping[str, Any], analysis: Mapping[str, Any] | None
) -> dict[str, str]:
    company = str(lead.get("company_name") or "your company").strip()
    contact = str(lead.get("contact_person") or "").strip()
    industry = str(lead.get("industry") or "").strip()
    greeting = f"Hi {contact}," if contact else "Hello,"

    body_lines = [greeting, "", f"I'm reaching out about {company}."]
    if industry:
        body_lines.append(f"I understand {company} is listed in the {industry} industry.")

    analysis_context = analysis or {}
    personalization = ""
    for key, label in (
        ("business_needs", "The saved company analysis noted"),
        ("opportunities", "The saved company analysis listed"),
        ("company_overview", "The saved company analysis describes"),
        ("industry_analysis", "The saved company analysis records"),
    ):
        value = analysis_context.get(key)
        if isinstance(value, str):
            items = [item.strip() for item in value.splitlines() if item.strip()]
        elif isinstance(value, list):
            items = [str(item).strip() for item in value if str(item).strip()]
        else:
            items = []
        if items:
            personalization = f"{label}: {items[0]}"
            break

    description = str(lead.get("description") or "").strip()
    if personalization:
        body_lines.extend(["", personalization])
    elif description:
        body_lines.extend(["", f"Your company notes mention: {description}"])

    body_lines.extend(
        [
            "",
            "Would you be open to a brief conversation to see whether this is relevant?",
            "",
            "Best,",
            "[Your name]",
        ]
    )
    return {
        "subject": f"A note for {company}",
        "body": "\n".join(body_lines),
    }


def generate_personalized_email(
    lead: Mapping[str, Any], analysis: Mapping[str, Any] | None = None
) -> dict[str, str]:
    """Create a reviewable email draft using only the supplied lead and analysis."""
    api_key = get_gemini_api_key()
    if not api_key:
        return _fallback_email_draft(lead, analysis)

    client = genai.Client(api_key=api_key)
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    source_data = {
        "lead": {key: value for key, value in lead.items() if value is not None},
        "saved_company_analysis": dict(analysis) if analysis else None,
    }
    prompt = f"""
    Write a concise, professional sales email draft based only on the source data below.
    Do not add company facts, infer needs, claim research was performed, or imply prior
    contact. Use only a recorded contact person's name when available; otherwise use a
    neutral greeting. If the source data has no useful personalization, keep the message
    brief rather than inventing details. This is a draft for a person to review; do not
    send it.

    Source data:
    {json.dumps(source_data, ensure_ascii=True)}

    Return only a valid JSON object with non-empty string fields "subject" and "body".
    """
    response = client.models.generate_content(model=model, contents=prompt)
    raw = getattr(response, "text", None)
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("The AI returned an empty email draft.")

    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if len(lines) < 3 or not lines[-1].strip().startswith("```"):
            raise ValueError("The AI returned an incomplete email draft.")
        raw = "\n".join(lines[1:-1]).strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("The AI returned invalid JSON for the email draft.") from exc

    if not isinstance(result, dict):
        raise ValueError("The AI email draft must be a JSON object.")
    subject = result.get("subject")
    body = result.get("body")
    if (
        not isinstance(subject, str)
        or not subject.strip()
        or not isinstance(body, str)
        or not body.strip()
    ):
        raise ValueError("The AI email draft must include a subject and body.")

    return {"subject": subject.strip(), "body": body.strip()}


def score_lead(
    lead: Mapping[str, Any], analysis: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Return a transparent heuristic score, not a conversion probability."""
    score = 0
    factors: list[str] = []

    core_points = 0
    for key, label in (("company_name", "Company name"), ("industry", "Industry")):
        if str(lead.get(key) or "").strip():
            core_points += 10
        else:
            factors.append(f"No {label.lower()} recorded: +0/10.")
    score += core_points
    if core_points:
        factors.append(f"Recorded company name and industry: +{core_points}/20.")

    profile_points = 0
    profile_fields = (
        ("contact_person", "Contact person", 10),
        ("email", "Email address", 10),
        ("description", "Company notes", 10),
        ("employee_count", "Employee count", 5),
        ("location", "Location", 5),
        ("website", "Website", 5),
        ("technology_stack", "Technology stack", 5),
    )
    for key, label, points in profile_fields:
        if str(lead.get(key) or "").strip():
            profile_points += points
        else:
            factors.append(f"No {label.lower()} recorded: +0/{points}.")
    score += profile_points
    factors.append(f"Available lead profile details: +{profile_points}/50.")

    if analysis and analysis.get("qualification_score") is not None:
        try:
            analysis_score = max(
                0, min(100, int(analysis["qualification_score"]))
            )
        except (TypeError, ValueError, OverflowError):
            analysis_score = None
        if analysis_score is not None:
            analysis_points = round(analysis_score * 0.2)
            score += analysis_points
            factors.append(
                f"Saved company-analysis qualification ({analysis_score}/100): "
                f"+{analysis_points}/20."
            )
        else:
            factors.append("Saved company-analysis score is invalid: +0/20.")
    else:
        factors.append("No saved company analysis: +0/20.")

    status_points = {
        "new": 3,
        "contacted": 5,
        "qualified": 8,
        "proposal": 9,
        "won": 10,
        "lost": 0,
    }
    status = str(lead.get("status") or "").strip()
    engagement_points = status_points.get(status.casefold(), 0)
    score += engagement_points
    factors.append(
        f"Recorded pipeline stage ({status or 'unknown'}): "
        f"+{engagement_points}/10; no interaction history is stored."
    )

    score = max(0, min(100, score))
    if score >= 70:
        label = "High qualification"
    elif score >= 40:
        label = "Developing"
    else:
        label = "Needs more information"

    return {
        "score": score,
        "qualification_label": label,
        "factors": factors,
        "score_basis": (
            "Heuristic based on recorded profile completeness, saved company "
            "analysis, and pipeline stage; it is not a conversion probability."
        ),
    }


def recommend_outreach(
    lead: Mapping[str, Any], analysis: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Recommend a next step using saved lead details and the recorded pipeline stage."""
    status = str(lead.get("status") or "New").strip()
    normalized_status = status.casefold()
    email_available = bool(str(lead.get("email") or "").strip())
    phone_available = bool(str(lead.get("phone") or "").strip())
    channel = "Email" if email_available else "Phone" if phone_available else None
    has_personalization = bool(
        str(lead.get("description") or "").strip()
        or (
            analysis
            and any(
                analysis.get(key)
                for key in (
                    "business_needs",
                    "opportunities",
                    "company_overview",
                    "industry_analysis",
                )
            )
        )
    )
    missing_information: list[str] = []
    if not email_available and not phone_available:
        missing_information.append("Email address or phone number")
    if not has_personalization:
        missing_information.append("Company notes or a saved company analysis")

    if normalized_status in {"won", "lost"}:
        return {
            "recommended_next_action": (
                "Pause prospecting and review the recorded pipeline stage before any future outreach."
            ),
            "suggested_channel": "No prospecting outreach",
            "follow_up_timing": "No follow-up recommended for the current stage.",
            "engagement_sequence": [
                "Review the lead status before planning any further communication."
            ],
            "information_sufficient": bool(channel and has_personalization),
            "missing_information": missing_information,
        }

    if not channel or not has_personalization:
        return {
            "recommended_next_action": (
                "Complete the missing lead details before sending personalized outreach."
            ),
            "suggested_channel": channel or "Not available; verify contact details",
            "follow_up_timing": "Set timing after a valid contact method and useful context are recorded.",
            "engagement_sequence": [
                "Add a contact email or phone number.",
                "Add company notes or generate a company analysis.",
                "Review a personalized draft before contacting the lead.",
            ],
            "information_sufficient": False,
            "missing_information": missing_information,
        }

    follow_up_interval = {
        "new": "3-5 business days after the initial outreach",
        "contacted": "3-5 business days",
        "qualified": "1-2 business days",
        "proposal": "3 business days",
    }.get(normalized_status, "3-5 business days")
    timing = {
        "new": f"Follow up {follow_up_interval} if there is no response.",
        "contacted": f"Follow up in {follow_up_interval}; no interaction history is recorded.",
        "qualified": f"Review the next step in {follow_up_interval}.",
        "proposal": f"Check in after {follow_up_interval} if no response is recorded.",
    }.get(
        normalized_status,
        f"Review the next step in {follow_up_interval}; no interaction history is recorded.",
    )
    if normalized_status == "new":
        action = f"Send a personalized introductory {channel.lower()} draft for review."
    else:
        action = (
            f"Prepare a concise {channel.lower()} follow-up using the saved lead details "
            "and company analysis."
        )

    personalization_source = (
        "saved company analysis" if analysis else "recorded company notes"
    )
    return {
        "recommended_next_action": action,
        "suggested_channel": channel,
        "follow_up_timing": timing,
        "engagement_sequence": [
            f"Review the lead details and {personalization_source} before outreach.",
            f"Send the reviewed {channel.lower()} message.",
            f"If there is no response, follow up after {follow_up_interval}.",
            "Record the interaction in the lead status; detailed engagement history is not currently stored.",
        ],
        "information_sufficient": True,
        "missing_information": missing_information,
    }


def generate_ai_response(prompt: str) -> dict:
    api_key = get_gemini_api_key()
    if not api_key:
        raise RuntimeError("Gemini API key is missing")

    client = genai.Client(api_key=api_key)
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    response = client.models.generate_content(
        model=model,
        contents=prompt
    )

    raw = (response.text or "").strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    return json.loads(raw)


def generate_email(lead, service, tone, context=None):
    api_key = get_gemini_api_key()
    if not api_key:
        company = lead.get("company_name", "your company")
        contact = lead.get("contact_person", "there")
        greeting = f"Hi {contact}," if contact else "Hello,"
        return {
            "subject": f"Partnership opportunity with {company}",
            "body": f"{greeting}\n\nI hope this email finds you well. I am reaching out to explore potential collaboration opportunities between our teams, particularly around {service}.\n\nLooking forward to connecting.\n\nBest regards,\nSales Team"
        }

    prompt = f"""
    You are a professional B2B sales email writer.

    Generate a personalized sales email.

    COMPANY INFORMATION:

    Company: {lead.get('company_name', '')}
    Industry: {lead.get('industry', '')}
    Contact: {lead.get('contact_person', '')}
    Website: {lead.get('website', '')}
    Technology: {lead.get('technology_stack', '')}
    Description: {lead.get('description', '')}

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
    api_key = get_gemini_api_key()
    if not api_key:
        return {
            "channel": "Email",
            "follow_up_timing": "Within 48 hours",
            "strategy": f"Initiate initial outreach highlighting relevant solutions for {lead.get('company_name', 'prospect')}.",
            "next_action": "Send personalized introductory email and schedule follow-up call."
        }

    prompt = f"""
    You are an AI sales strategy assistant.

    Analyse this prospect and generate an outreach strategy.

    COMPANY:
    {lead.get('company_name', '')}

    INDUSTRY:
    {lead.get('industry', '')}

    BUSINESS DESCRIPTION:
    {lead.get('description', '')}

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
