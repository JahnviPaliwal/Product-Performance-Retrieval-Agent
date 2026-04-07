"""
reasoning_agent.py
Takes the retrieval output from retrieval_agent.py and uses the LLM
to reason over it and produce a final, grounded answer.
"""

import json
from groq import Groq

client = Groq()
MODEL  = "llama-3.1-8b-instant"


def reason_and_answer(user_query: str, retrieval_output: dict) -> dict:
    """
    Given the user's question and retrieved context (SQL rows + text chunks),
    asks the LLM to synthesise a final answer with a reasoning trace.

    Returns a dict:
        {
          "answer":          str,
          "reasoning_trace": str,
        }
    """

    # Format context for the LLM
    sql_context  = json.dumps(retrieval_output["sql_results"], indent=2)
    text_context = "\n\n".join(retrieval_output["text_chunks"])

    prompt = f"""You are a helpful data analyst assistant.

You have been given two sources of information to answer the user's question:

--- STRUCTURED DATA (from SQL database) ---
{sql_context}

--- UNSTRUCTURED TEXT (from documents) ---
{text_context}

User question: {user_query}

Instructions:
1. First, write a "Reasoning Trace" section where you explain step-by-step how
   you interpret the data and arrive at your answer.
2. Then write a "Final Answer" section with a clear, concise response.

Format your output EXACTLY like this:
REASONING TRACE:
<your step-by-step reasoning here>

FINAL ANSWER:
<your concise answer here>
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    content = response.choices[0].message.content.strip()

    # Parse the two sections
    reasoning_trace = ""
    final_answer    = content  # fallback: show full response

    if "FINAL ANSWER:" in content:
        parts           = content.split("FINAL ANSWER:")
        reasoning_trace = parts[0].replace("REASONING TRACE:", "").strip()
        final_answer    = parts[1].strip()

    return {
        "answer":          final_answer,
        "reasoning_trace": reasoning_trace,
    }
