from app.core.config import settings


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

    provider = provider.lower()

    if provider == "groq":
        return _call_groq(prompt, api_key or settings.GROQ_API_KEY)
    elif provider == "openai":
        return _call_openai(prompt, api_key)
    elif provider == "anthropic":
        return _call_anthropic(prompt, api_key)
    elif provider == "gemini":
        return _call_gemini(prompt, api_key)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


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
        model="claude-opus-4-6",
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
