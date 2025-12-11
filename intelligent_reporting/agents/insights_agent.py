import json
import os
from typing import Any, Dict, List

from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
from intelligent_reporting.agents.fallback_manager import get_fallback_llm
from scripts.utils import json_fix, strip_code_fence


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
    offline_mode: bool = False,
) -> Any:
    if offline_mode:
        llm = get_fallback_llm(task_type="vision")
    else:
        llm = AzureChatOpenAI(
            azure_deployment="gpt-5-nano",  # The name you gave the model in Azure AI Studio
            api_version="2024-12-01-preview",  # Check Azure for your specific version
            azure_endpoint=os.getenv("AZURE_ENDPOINT"),
            api_key=os.getenv("API_KEY"),
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
        content = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )
        raw = strip_code_fence(content)
        fixed = json_fix(raw)
        if not isinstance(fixed, str):

            fixed = json.dumps(fixed)
        return fixed
    except Exception as e:
        print(Exception(f"Failed to generate insights: {str(e)}"))
        llm = get_fallback_llm(task_type="vision")
        response = llm.invoke(messages)
        content = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )
        raw = strip_code_fence(content)
        fixed = json_fix(raw)
        if not isinstance(fixed, str):

            fixed = json.dumps(fixed)
        return json_fix(response.content)
