import json

from langchain_ollama import ChatOllama
from langchain.messages import HumanMessage, SystemMessage


def insights_query(img, summary_data, sample_data, description):
    """Run a prompt through local Ollama using LangChain integration."""
    llm = ChatOllama(
        model="qwen3-vl:235b-cloud",
        temperature=0.2,
    )

    llm_prompt = [
        SystemMessage(
            content=(
                "You are a senior data analyst. "
                "Your job is to extract concise, high-value insights using: "
                "1) the dataset summary, 2) the high-level description, and 3) the provided image. "
                "Respond only with valid JSON. "
                "The JSON must be an array of objects, each with: "
                '"insight", "reasoning", "evidence".'
            )
        ),
        HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": f"""
                    Use the data summary, description, and image to produce insights.

                    Respond strictly in this JSON format:

                    [
                    {{
                        "insight": " insight",
                        "reasoning": "why it matters",
                        "evidence": "specific numbers or image details"
                    }}
                    ]

                    Data_Summary: {json.dumps(summary_data)}
                    Data_Sample: {json.dumps(sample_data)}
                    High_Level_Description: {json.dumps(description)}
                    """,
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img}"},
                },
            ]
        ),
    ]

    try:
        response = llm.invoke(llm_prompt)
        return response.content.strip()

    except Exception as e:
        raise e
