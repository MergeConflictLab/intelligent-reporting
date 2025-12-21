from typing import Dict, List
import json

# from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
import os
from scripts.utils import json_fix, strip_code_fence

def supervisor_query(
    sample_data: List[Dict],
    description: List[Dict],
):
    """Run a prompt through local Ollama using LangChain integration."""
    llm = AzureChatOpenAI(
    azure_deployment="gpt-5-nano",  # The name you gave the model in Azure AI Studio
    api_version="2024-12-01-preview",           # Check Azure for your specific version
    azure_endpoint= os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("API_KEY"),
)
    llm_prompt = [
        SystemMessage(
            content=(
                """
You are the Supervisor Agent in a multi-agent analytics system.
Your job is to read the dataset metadata and sample rows, then produce a clear, unambiguous analysis plan for the Code Generator Agent (Assistant Agent).
You must output a JSON object that follows this exact schema:
{
    "libraries": ["pandas", "numpy", "matplotlib", "seaborn"],
    "tasks": [
        {
        "name": "short_title",
        "description": "what insight this plot or analysis provides",
        "columns": ["colA", "colB"],
        "plot_type": "histogram | line | bar | scatter | box | heatmap | table | summary_stat",
        "preprocessing": "describe transformations if needed: dropna, filter, groupby, dtype conversion, etc.",
        "code_template": "pseudo-code only (not executable), describing how the Assistant should implement it"
        }
    ]
}
Rules:
- Only use columns explicitly mentioned in metadata or sample rows.
- Never invent columns or derived values unless explicitly described.
- Each task must represent exactly one plot or one analysis.
- Keep tasks simple and atomic.
- No explanations outside the JSON.
- No Python code. Only pseudo-code inside code_template.
- The output must ALWAYS be valid JSON.
- Be concise but precise.
            """
            )
        ),
        HumanMessage(
            content=f"""
            Dataset Metadata:
                {json.dumps(description)}
            Sample Rows:
                {json.dumps(sample_data)}
            Generate the task plan strictly following the schema above.
     """
        ),
    ]

    try:
        response = llm.invoke(llm_prompt)
        # Remove markdown/code fences and attempt to parse JSON
        content = strip_code_fence(response.content)
        parsed = json_fix(content)
        return parsed

    except Exception as e:
        raise e
