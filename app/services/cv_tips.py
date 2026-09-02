"""Legacy single-provider (Groq-only) CV tip generator.

Not imported anywhere in the current codebase — superseded by the
multi-provider `app.services.llm.get_cv_tips`, which is what
`app/api/v1/cv.py` actually calls. Kept only for reference; safe to delete
once confirmed unnecessary.
"""

from groq import Groq

from app.core.config import settings
from app.models.job import Job


def get_cv_tips(job: Job, cv_text: str) -> str:
    """Generate 5 CV tailoring tips for a job using Groq directly.

    Args:
        job: The Job row to tailor the CV against.
        cv_text: Plain text extracted from the candidate's CV file.

    Returns:
        Raw LLM response text containing 5 tips.
    """
    client = Groq(api_key=settings.GROQ_API_KEY)

    prompt = (
        f"Job title: {job.title}\n"
        f"Company: {job.company}\n"
        f"Location: {job.location or 'Not specified'}\n\n"
        f"CV:\n{cv_text}\n\n"
        "Give 5 concise, specific tips to tailor this CV for the job above. "
        "Focus on what to highlight, reword, add, or remove. Be direct and actionable."
    )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.7,
    )

    return response.choices[0].message.content
