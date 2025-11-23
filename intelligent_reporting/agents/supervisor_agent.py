from typing import Dict, List
import json

# from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, SystemMessage


def supervisor_query(
    model: str,
    sample_data: List[Dict],
    description: List[Dict],
):
    """Run a prompt through local Ollama using LangChain integration."""
    llm = ChatOllama(
        model=model,
        temperature=0.1,
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

        return response.content.strip()

    except Exception as e:
        raise e
