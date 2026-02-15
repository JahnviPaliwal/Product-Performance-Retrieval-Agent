from groq import Groq
import json
import re

MODEL = "llama-3.1-8b-instant"


def _safe_json_extract(text):
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def recommend_insights(profile, api_key):
    client = Groq(api_key=api_key)

    prompt = f"""
Return ONLY valid JSON.

Dataset profile:
{json.dumps(profile, indent=2)}

Choose exactly 6 insights from:
distribution, missing_data, categorical_patterns,
relationships, outliers, schema

JSON format:
[
  {{
    "title": "...",
    "description": "...",
    "insight_type": "distribution | missing_data | categorical_patterns | relationships | outliers | schema"
  }}
]
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    parsed = _safe_json_extract(response.choices[0].message.content)
    # return parsed


    if parsed is None:
    
        return [
            {
                "title": "Dataset structure overview",
                "description": "Understand column types and schema",
                "insight_type": "schema"
            },
            {
                "title": "Missing values check",
                "description": "Identify missing data issues",
                "insight_type": "missing_data"
            },
            {
                "title": "Numerical distributions",
                "description": "Summary statistics of numeric columns",
                "insight_type": "distribution"
            },
            {
                "title": "Category frequency patterns",
                "description": "Most common categorical values",
                "insight_type": "categorical_patterns"
            },
            {
                "title": "Feature relationships",
                "description": "Correlations between numeric columns",
                "insight_type": "relationships"
            },
            {
                "title": "Outlier detection",
                "description": "Unusual values in numeric data",
                "insight_type": "outliers"
            }
        ]

    return parsed


def answer_followup(profile, insight_title, insight_result, user_question):
    prompt = f"""
You are a careful data analyst.

Dataset profile:
{json.dumps(profile, indent=2)}

Insight title:
{insight_title}

Insight result:
{str(insight_result)[:2000]}

Rules:
- Answer ONLY using the insight result
- If not answerable, say:
  "This cannot be determined from the current analysis."

User question:
{user_question}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()
