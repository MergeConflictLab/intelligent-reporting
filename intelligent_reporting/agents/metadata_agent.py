import json
from typing import Dict, List, Any
import os

from langchain.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from .fallback_manager import get_fallback_llm
from scripts.utils import json_fix, strip_code_fence
from .base_agent import Agent


class MetadataAgent(Agent):
    """
    Agent responsible for summarizing dataset structure.
    """

    def run(
        self,
        sample_data: List[Dict],
        schema: Dict[str, str],
        description: List[Dict],
        offline_mode: bool = False,
    ) -> str:
        """Run a prompt through Ollama using LangChain integration or Fallback LLM."""
        print(f"[{self.__class__.__name__}] Starting execution...")

        if offline_mode:
            llm = get_fallback_llm(task_type="text")
        else:
            try:
                from langchain_openai import AzureChatOpenAI

                llm = AzureChatOpenAI(
                    azure_deployment="gpt-5-nano",
                    api_version="2024-12-01-preview",
                    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
                    api_key=os.getenv("API_KEY"),
                )
            except ImportError:
                print(
                    f"[{self.__class__.__name__}] 'langchain_openai' not found. Forcing offline mode."
                )
                llm = get_fallback_llm(task_type="text")

        llm_prompt = [
            SystemMessage(
                content="""
    You are a data analyst.
    Summarize the dataset structure based on the provided schema.
    Respond **only** in JSON with keys 'table_description' and 'columns', where 'columns' is a list of column summaries with actual text descriptions about each column.
    """
            ),
            HumanMessage(
                content=f"""
    Use the following format:
    {{
        "table_description": "A brief summary of the table contents.",
        "columns": [
            {{
                "name": "column_name",
                "description": "A brief description of the column."
            }},...
        ]
    }}

            Data: {json.dumps(sample_data)}
            Schema: {json.dumps(schema)}
            Column details: {json.dumps(description)}
            """
            ),
        ]

        try:
            response = llm.invoke(llm_prompt)
            content = strip_code_fence(response.content)
            parsed = json_fix(content)

            print(f"[{self.__class__.__name__}] Execution completed successfully.")
            print(f"[{self.__class__.__name__}] Output: {json.dumps(parsed, indent=2)}")
            return parsed
        except Exception as e:
            print(f"[{self.__class__.__name__}] Error: {e}, using fallback...")

            llm = get_fallback_llm(task_type="text")
            response = llm.invoke(llm_prompt)
            return json_fix(response.content.strip())
