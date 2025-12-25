import json
import os
from typing import Any, Dict, List

from langchain.messages import HumanMessage, SystemMessage

from .base_agent import Agent
from scripts.utils import json_fix, strip_code_fence

# IF IT IS ENDURABLE THEN ENDURE IT. STOP COMPLAINING - MARCUS AURELIUS IN MEDITATIONS


class InsightsAgent(Agent):
    """
    Agent responsible for generating insights from plots using Ollama Qwen-VL.
    """

    def run(
        self,
        img: str,
        summary_data: Dict,
        sample_data: List[Dict],
        description: Dict,
        offline_mode: bool = False,
    ) -> Any:
        """Run a prompt through Ollama Qwen-VL using LangChain integration or Fallback LLM."""
        print(f"[{self.__class__.__name__}] Starting execution...")

        if offline_mode:
            from langchain_ollama import ChatOllama

            llm = ChatOllama(model="qwen3-vl:4b")
        else:
            from langchain_openai.chat_models.azure import AzureChatOpenAI

            llm = AzureChatOpenAI(
                azure_deployment="gpt-5-nano",
                api_version="2024-12-01-preview",
                azure_endpoint=os.getenv("AZURE_ENDPOINT"),
                api_key=os.getenv("API_KEY"),
            )

        system_message = SystemMessage(
            content="""
You are a Data Science expert.
Analyze the provided plot and the metadata.
Provide a concise, high-level insight in JSON format.
The keys should be:
- 'observation': What does the plot show?
- 'insight': What does it mean for the business?
- 'actionable': What should be done next?
"""
        )

        human_message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": f"""
Dataset Summary: {json.dumps(summary_data)}
Sample Data: {json.dumps(sample_data)}
Task Description: {json.dumps(description)}
""",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img}"},
                },
            ]
        )

        try:
            response = llm.invoke([system_message, human_message])
            content = strip_code_fence(response.content)
            parsed = json_fix(content)

            print(f"[{self.__class__.__name__}] Execution completed successfully.")
            print(f"[{self.__class__.__name__}] Output: {json.dumps(parsed, indent=2)}")

            return parsed

        except Exception as e:
            print(f"[{self.__class__.__name__}] Error: {str(e)}")
            raise RuntimeError(f"Failed to generate insight with Ollama: {str(e)}")
