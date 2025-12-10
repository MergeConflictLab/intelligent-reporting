import toon
from langchain.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
import os
from langchain_openai import AzureChatOpenAI
from scripts.utils import strip_code_fence, json_fix


def assistant_query(supervisor_response, path):
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
You generate Python code only. No comments, no markdown, no explanations.
Output format must be:
FIRST LINE: a short snake_case task name.
REST: valid Python code.
Rules:
- Only use pandas, numpy, matplotlib, seaborn, plotly.
- Load the dataset into df from the given path.
- If randomness: np.random.seed(42).
- Use plt.savefig(), never plt.show().
- No file I/O except saving plots.
- Use only columns mentioned by the supervisor; skip missing ones.
"""
            )
        ),
        HumanMessage(
            content=(
                f"""
Supervisor plan: {toon.encode(supervisor_response)}
Dataset path: {path}
Return ONLY a task name on the first line and Python code starting on the second line.
                """
            )
        ),
    ]

    try:
        response = llm.invoke(llm_prompt)
        # Normalize output: remove markdown/code fences and attempt simple json fix
        raw = strip_code_fence(response.content)
        # json_fix will return the input unchanged if it's not JSON, so it's safe here
        fixed = json_fix(raw)
        if not isinstance(fixed, str):
            # If json_fix parsed JSON (unlikely for assistant), convert back to string
            import json as _json

            fixed = _json.dumps(fixed)

        name, code = fixed.split("\n", 1)
        name = name.strip()
        code = code.strip()

        return {"name": name, "code": code}

    except Exception as e:
        raise e
