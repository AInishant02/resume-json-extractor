# Structured LLM Prompt Pipeline & JSON Extractor

A Python pipeline that turns unstructured resume text into **strictly validated JSON** using the Google Gemini API, parameterized prompt templates with few-shot examples, and Pydantic schema validation.

## How it works

```
resume .txt  ->  prompt template (+ schema + few-shot)  ->  Gemini  ->  JSON
                                                                         |
                       valid -> saved to output/       <-  Pydantic validation
                       invalid -> errors sent back to Gemini, retry (max 3)
```

1. **Parameterized prompt** (`prompts.py`): a system prompt template filled at runtime with the document type and the Resume JSON schema, plus two few-shot examples (raw text in, correct JSON out).
2. **Gemini call** (`extractor.py`): requests JSON output at temperature 0, with backoff on temporary API errors (429/503).
3. **Strict validation** (`schemas.py`): Pydantic models check types, formats and cross-field rules.
4. **Self-correcting retry loop**: if validation fails, the model's own output and the exact error messages are sent back so it can fix them (up to 3 attempts).
5. **Not-a-resume guard**: the model can answer `{"error": "not_a_resume"}`, which stops the pipeline immediately instead of forcing made-up data.

## Validation rules

| Field | Rule |
|---|---|
| `full_name` | min 2 characters, placeholders like "Unknown" / "N/A" rejected |
| `email` | must be a valid email format (or null) |
| `skills` | at least 1 skill; duplicates removed; placeholders rejected |
| `education.start_year / end_year` | integers between 1950 and 2100; end not before start |
| `experience.start_date / end_date` | `YYYY-MM` format (year-only `YYYY` also accepted); end not before start |
| `experience.is_current` | if true, `end_date` must be null |

Missing information is returned as `null` (or an empty list), never invented.

## Setup

**Requirements:** Python 3.10+ and a free Gemini API key from Google AI Studio.

```bash
# Windows
setup.bat

# macOS / Linux / Git Bash
./setup.sh
```

Then open `.env` and fill in:

```
GEMINI_API_KEY=your_key_here
MODEL=gemini-3.8-flash
```

Verify the connection:

```bash
python test_connection.py     # should print: ready
```

## Usage

Extract one resume:

```bash
python main.py samples/resume1.txt
python main.py samples/resume1.txt --out output/custom.json
python main.py samples/resume1.txt --quiet
```

Run all sample files and print a summary table:

```bash
python run_all.py
```

Self-tests for individual modules:

```bash
python schemas.py     
python prompts.py    
python extractor.py   
```

## Project structure

```
.env.example         # template for your API key and model name
requirements.txt
setup.bat / setup.sh # one-command environment setup
test_connection.py   # API key / model smoke test
schemas.py           # Pydantic Resume schema + validators
prompts.py           # prompt template + few-shot examples
extractor.py         # Gemini call + validation + retry loop
main.py              # CLI entry point
run_all.py           # batch test runner with summary table
samples/             # test inputs (clean, messy, missing fields, not a resume)
output/              # generated JSON
```

## Test inputs

| File | What it tests |
|---|---|
| `resume1.txt` | Clean, well-formatted resume |
| `resume2_messy.txt` | Informal text ("march 2023 till now", lowercase, `//` separators) |
| `resume3_missing_fields.txt` | Minimal resume: missing phone, experience, location |
| `not_a_resume.txt` | Non-resume text, which must be rejected |

## Example

Input (`samples/resume3_missing_fields.txt`):

```
Priya Nair
Email: priya.nair@example.com

Education
MBA, IIM Indore, 2020-2022

Skills: Excel, Tableau, SQL
```

Output:

```json
{
  "full_name": "Priya Nair",
  "email": "priya.nair@example.com",
  "phone": null,
  "location": null,
  "summary": null,
  "education": [
    {
      "degree": "MBA",
      "institution": "IIM Indore",
      "start_year": 2020,
      "end_year": 2022,
      "grade": null
    }
  ],
  "experience": [],
  "skills": ["Excel", "Tableau", "SQL"],
  "certifications": []
}
```

Missing fields come back as `null` or empty, and nothing is invented.

## Results

| File | What it tests | Result |
|---|---|---|
| `resume1.txt` | Clean, well-formatted resume | PASS: valid JSON on attempt 1 |
| `resume2_messy.txt` | Informal text, lowercase, year-only dates | PASS: valid JSON on attempt 1, dates normalized, current job detected |
| `resume3_missing_fields.txt` | Minimal resume with missing fields | PASS: valid JSON on attempt 1, missing fields returned as `null` |
| `not_a_resume.txt` | Non-resume input | REJECTED: "Input does not look like a resume" |

All 3 resume inputs produced schema-valid JSON, and the non-resume input was correctly rejected instead of being filled with made-up values. Samples were run in separate sessions because of the free tier's daily request limit.

## Design notes and lessons learned

- **Validation catches what the model gets wrong.** In testing, the model sometimes failed validation on the first attempt (for example, wrong date formats) and fixed itself on the retry once it saw the exact error.
- **Models fabricate to satisfy a schema.** Given a grocery list, the model filled `"Unknown"` into required fields to pass validation. Fixed with three layers: an explicit `not_a_resume` escape hatch in the prompt, the same instruction repeated in the retry message, and schema validators that reject placeholder values.
- **Schema validators run locally.** Gemini's structured-output option does not enforce Pydantic validators, so the schema is included in the prompt and all strict rules are enforced by Pydantic after the response.
- **SDK choice.** This project uses the current official `google-genai` SDK (successor to `google-generativeai`), which covers the same requirement.

## Known limitations

- Free-tier Gemini keys have low daily request limits (about 20 per day for the model used here). Each file takes 1 to 3 requests, so run `run_all.py` sparingly. The script pauses between files and retries temporary 429/503 errors.
- Input is plain `.txt`. PDF/DOCX parsing is not included.
- A skills or tech-stack line can occasionally be placed into an experience `highlights` list.