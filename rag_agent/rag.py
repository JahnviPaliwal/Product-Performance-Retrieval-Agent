import pandas as pd
from groq import Groq  # ❌ Fix: Use Groq, not openai
import tiktoken  # For token counting


def build_rag_answer(df: pd.DataFrame, prompt: str, api_key: str, analytics: str):
    client = Groq(api_key=api_key)  # ✅ Groq client

    # 🛡️ Token-safe context (limit to 2k tokens)
    context = f"""
    Dataset Columns: {list(df.columns)}
    Sample Rows (first 5): {df.head(5).to_string()}  # ❌ Fix: 10→5 rows
    Analytics: {analytics[:1000]}  # Truncate analytics
    """

    # 🛡️ Estimate tokens (rough: 1 token ≈ 4 chars)
    context_tokens = len(context) // 4 + 100  # Safety margin
    if context_tokens > 2500:
        context = context[:8000]  # Hard truncate

    system_prompt = """
    You are an AI data analyst.
    Answer ONLY using provided dataset context.
    Perform calculations if needed.
    Explain clearly in 300 words max.
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{context}\n\nQuestion: {prompt}"}
        ],
        max_tokens=600,  # 🛡️ SAFE output limit
        temperature=0.1
    )

    # 🛡️ Usage tracking
    tokens_used = response.usage.total_tokens
    print(f"🛡️ Tokens used: {tokens_used}/6000 TPM")  # Monitor

    return response.choices[0].message.content
