import json
from typing import Dict, List, Any

from langchain_ollama import ChatOllama
from langchain.messages import HumanMessage, SystemMessage

from scripts.utils import json_fix


JSON_SCHEMA_TEMPLATE = """[
{{
    "insight": "insight",
    "reasoning": "why it matters",
    "evidence": "specific numbers or image details"
}}
]"""


def insights_query(
    img: str,
    summary_data: Dict[str, Any],
    sample_data: List[Dict[str, Any]],
    description: str,
    story_mode: bool = False,
) -> Any:

    llm = ChatOllama(
        model="qwen3-vl:235b-cloud",
        temperature=0.2,
    )

    system_prompt = (
        "You are a senior data analyst and storytelling master. "
        "Extract concise, high-value insights and tell detailed stories suitable"
        "for both technical and non-technical audiences using: "
        "1) the dataset summary, 2) the metadata description, and 3) the provided image. "
        "Respond only with valid JSON. "
        "The JSON must be an array of objects with: "
        '"insight", "reasoning", "evidence".'
    )

    instruction = (
        "Use the data summary, metadata, and image to produce one high valuable insight."
        if story_mode
        else "Use the data summary, description, and image to produce insights."
    )
    user_prompt = f"""
        {instruction}
        Respond strictly in this JSON format:
        {JSON_SCHEMA_TEMPLATE}
        context:
        Data_Summary: {json.dumps(summary_data)}
        Data_Sample: {json.dumps(sample_data)}
        High_Level_Description: {json.dumps(description)}
    """

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=[
                {"type": "text", "text": user_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img}"},
                },
            ]
        ),
    ]

    try:
        response = llm.invoke(messages)
        return json_fix(response.content)
    except Exception as e:
        raise Exception(f"Failed to generate insights: {str(e)}") from e