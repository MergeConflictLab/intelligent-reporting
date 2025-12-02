import json

from langchain_ollama import ChatOllama
from langchain.messages import HumanMessage, SystemMessage

from scripts.utils import json_fix


def insights_query(
    img, summary_data, sample_data, description, story_mode: bool = False
):
    """Run a prompt through local Ollama using LangChain integration."""
    llm = ChatOllama(
        model="qwen3-vl:235b-cloud",
        temperature=0.2,
    )

    if story_mode:
        system_text = (
            "You are a senior data analyst and storytelling master. "
            "Extract concise, high-value insights and tell detailed stories suitable "
            "for both technical and non-technical audiences using: "
            "1) the dataset summary, 2) the metadata description, and 3) the provided image. "
            "Respond only with valid JSON. "
            "The JSON must be an array of objects with: "
            '"insight", "reasoning", "evidence".'
        )

        user_text = f"""
            Use the data summary, metadata, and image to produce one high valuable insight.

            Respond strictly in this JSON format:

            [
            {{
                "insight": "insight",
                "reasoning": "why it matters",
                "evidence": "specific numbers or image details"
            }}
            ]

            Data_Summary: {json.dumps(summary_data)}
            Data_Sample: {json.dumps(sample_data)}
            High_Level_Description: {json.dumps(description)}
        """
    else:
        system_text = (
            "You are a senior data analyst. "
            "Your job is to extract concise, high-value insights using: "
            "1) the dataset summary, 2) the high-level description, and 3) the provided image. "
            "Respond only with valid JSON. "
            "The JSON must be an array of objects with: "
            '"insight", "reasoning", "evidence".'
        )

        user_text = f"""
            Use the data summary, description, and image to produce insights.

            Respond strictly in this JSON format:

            [
            {{
                "insight": "insight",
                "reasoning": "why it matters",
                "evidence": "specific numbers or image details"
            }}
            ]

            Data_Summary: {json.dumps(summary_data)}
            Data_Sample: {json.dumps(sample_data)}
            High_Level_Description: {json.dumps(description)}
        """

    llm_prompt = [
        SystemMessage(content=system_text),
        HumanMessage(
            content=[
                {"type": "text", "text": user_text},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img}"},
                },
            ]
        ),
    ]

    try:
        response = llm.invoke(llm_prompt)
        return json_fix(response.content)
    except Exception as e:
        raise e
