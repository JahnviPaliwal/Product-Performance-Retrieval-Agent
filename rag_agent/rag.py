import openai
import pandas as pd

def build_rag_answer(df: pd.DataFrame, prompt: str, api_key: str, analytics: str):
    openai.api_key = api_key

    context = f"""
    Dataset Columns: {list(df.columns)}
    Sample Rows:
    {df.head(10).to_string()}
    Analytics Results:
    {analytics}
    """

    system_prompt = """
    You are an AI data analyst.
    Answer ONLY using the provided dataset context.
    Perform calculations if needed.
    Explain clearly.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{prompt}"}
        ]
    )

    return response.choices[0].message.content
