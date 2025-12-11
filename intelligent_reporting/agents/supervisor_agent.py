import json
from typing import Dict, List

from langchain.messages import HumanMessage, SystemMessage


from intelligent_reporting.agents.fallback_manager import get_fallback_llm
from langchain_openai import AzureChatOpenAI
import os
from scripts.utils import json_fix, strip_code_fence


def supervisor_query(
    sample_data: List[Dict],
    description: List[Dict],
    offline_mode: bool = False,
) -> Dict:
    """Run a prompt through local Ollama using LangChain integration or Fallback LLM."""

    if offline_mode:
        llm = get_fallback_llm(task_type="text")
    else:
        llm = AzureChatOpenAI(
            azure_deployment="gpt-5-nano",
            api_version="2024-12-01-preview",
            azure_endpoint=os.getenv("AZURE_ENDPOINT"),
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
        print(Exception(f"Failed to generate task plan: {str(e)}"))
        llm = get_fallback_llm(task_type="text")
        response = llm.invoke(llm_prompt)
        return json_fix(response.content.strip())
