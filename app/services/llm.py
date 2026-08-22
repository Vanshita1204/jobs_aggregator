from app.core.config import settings

_PROVIDERS = {}


def _call_llm(prompt: str, provider: str, api_key: str | None) -> str:
    provider = (provider or "groq").lower()
    call = _PROVIDERS.get(provider)
    if not call:
        raise ValueError(f"Unsupported provider: {provider}")
    if provider == "groq":
        api_key = api_key or settings.GROQ_API_KEY
    return call(prompt, api_key)


def extract_job_data(page_text: str, provider: str = "groq", api_key: str | None = None) -> str:
    """
    Ask the LLM to extract job details from raw page text.
    Returns the raw LLM string (caller parses JSON).
    """
    prompt = (
        "Extract job posting details from the following webpage text.\n"
        "Return ONLY a valid JSON object with exactly these fields:\n"
        '{"title": "...", "company": "...", "location": "...", "description": "..."}\n'
        "Use empty string for any field not found. No extra text outside the JSON.\n\n"
        f"Webpage text:\n{page_text}"
    )
    return _call_llm(prompt, provider, api_key)


def get_cv_tips(
    job_title: str,
    company: str,
    location: str,
    cv_text: str,
    description: str = "",
    provider: str = "groq",
    api_key: str | None = None,
) -> str:
    job_section = (
        f"Job title: {job_title}\n"
        f"Company: {company}\n"
        f"Location: {location or 'Not specified'}\n"
    )
    if description:
        job_section += f"\nJob description:\n{description}\n"

    prompt = (
        f"{job_section}\n"
        f"CV:\n{cv_text}\n\n"
        "You are a senior recruiter reviewing this CV for the job above.\n"
        "Read the ENTIRE CV carefully, then give exactly 5 improvement suggestions.\n"
        "For each suggestion:\n"
        "- Quote or reference the specific CV line/section you are addressing\n"
        "- Explain what is wrong or missing\n"
        "- Give the exact reworded text or concrete addition to make\n\n"
        "Be blunt and specific. No generic advice. Every suggestion must be tied to actual content in the CV and the job description."
    )

    return _call_llm(prompt, provider, api_key)


def _call_groq(prompt: str, api_key: str) -> str:
    from groq import Groq

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
        temperature=0.7,
    )
    return response.choices[0].message.content


def _call_openai(prompt: str, api_key: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.7,
    )
    return response.choices[0].message.content


def _call_anthropic(prompt: str, api_key: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _call_gemini(prompt: str, api_key: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text


_PROVIDERS.update(
    {
        "groq": _call_groq,
        "openai": _call_openai,
        "anthropic": _call_anthropic,
        "gemini": _call_gemini,
    }
)
