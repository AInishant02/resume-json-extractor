"""Parameterized prompt templates + few-shot examples."""
import json

SYSTEM_PROMPT = """You are a precise data-extraction engine.
Extract information from the {doc_type} text provided by the user and return
ONLY a JSON object that matches the JSON schema below. No markdown, no commentary.

Rules:
- Never invent information. If a field is missing from the text, use null
  (or an empty list for list fields).
- Dates in experience must use the format YYYY-MM (e.g. "March 2023" -> "2023-03").
- If only a year is given for a date, use just the year (e.g. "2021"). Never invent a month.
- Normalize capitalization: proper-case names, locations and job titles (e.g. "Rohan Verma", "Bangalore", "Backend Developer"), and use standard forms for skills (e.g. "Python", "AWS", "Kubernetes"). Keep the grade exactly as written.
- If a job is ongoing ("present", "till now", "since"), set is_current to true
  and end_date to null.
- Education years must be integers (e.g. 2022).
- Keep the grade exactly as written in the text.
- Put each bullet point or achievement as a separate string in highlights.
- If the text is clearly not a resume or CV (for example a shopping list or an article), return exactly {{"error": "not_a_resume"}} and nothing else.

JSON schema:
{schema}
"""

# Each example: raw text in, correct JSON out.
FEW_SHOT_EXAMPLES = [
    {
        "input": (
            "Karan Mehta | karan.mehta@example.com | Mumbai\n"
            "Education: B.Sc IT, Mumbai University, 2018-2021, 7.9 CGPA\n"
            "Worked as Data Analyst at FinEdge (Jul 2021 - Dec 2023): built dashboards "
            "in Power BI, automated weekly reports.\n"
            "Skills: SQL, Power BI, Python"
        ),
        "output": {
            "full_name": "Karan Mehta",
            "email": "karan.mehta@example.com",
            "phone": None,
            "location": "Mumbai",
            "summary": None,
            "education": [
                {
                    "degree": "B.Sc IT",
                    "institution": "Mumbai University",
                    "start_year": 2018,
                    "end_year": 2021,
                    "grade": "7.9 CGPA",
                }
            ],
            "experience": [
                {
                    "title": "Data Analyst",
                    "company": "FinEdge",
                    "start_date": "2021-07",
                    "end_date": "2023-12",
                    "is_current": False,
                    "highlights": [
                        "Built dashboards in Power BI",
                        "Automated weekly reports",
                    ],
                }
            ],
            "skills": ["SQL", "Power BI", "Python"],
            "certifications": [],
        },
    },
    {
        "input": (
            "SNEHA IYER\n"
            "Chennai\n"
            "Product Designer at Pixelwise since February 2024.\n"
            "Previously UX intern at Freshworks, Jan 2023 to Jun 2023.\n"
            "Design: Figma, Prototyping, User Research\n"
            "Certified: Google UX Design Certificate"
        ),
        "output": {
            "full_name": "Sneha Iyer",
            "email": None,
            "phone": None,
            "location": "Chennai",
            "summary": None,
            "education": [],
            "experience": [
                {
                    "title": "Product Designer",
                    "company": "Pixelwise",
                    "start_date": "2024-02",
                    "end_date": None,
                    "is_current": True,
                    "highlights": [],
                },
                {
                    "title": "UX Intern",
                    "company": "Freshworks",
                    "start_date": "2023-01",
                    "end_date": "2023-06",
                    "is_current": False,
                    "highlights": [],
                },
            ],
            "skills": ["Figma", "Prototyping", "User Research"],
            "certifications": ["Google UX Design Certificate"],
        },
    },
]


def build_prompt(doc_type: str, schema: dict, text: str):
    """Fill the template and return (system_instruction, contents) for Gemini."""
    system_instruction = SYSTEM_PROMPT.format(
        doc_type=doc_type, schema=json.dumps(schema, indent=2)
    )

    contents = []
    for ex in FEW_SHOT_EXAMPLES:
        contents.append({"role": "user", "parts": [{"text": ex["input"]}]})
        contents.append({"role": "model", "parts": [{"text": json.dumps(ex["output"])}]})
    contents.append({"role": "user", "parts": [{"text": text}]})

    return system_instruction, contents


if __name__ == "__main__":
    # Self-test: make sure our few-shot examples are themselves valid.
    from schemas import Resume

    for i, ex in enumerate(FEW_SHOT_EXAMPLES, 1):
        Resume.model_validate(ex["output"])
        print(f"Few-shot example {i}: OK")

    system, contents = build_prompt("resume", Resume.model_json_schema(), "sample text")
    print(f"Messages built: {len(contents)} (expected 5)")
    print("\n--- first 400 chars of system prompt ---")
    print(system[:400])