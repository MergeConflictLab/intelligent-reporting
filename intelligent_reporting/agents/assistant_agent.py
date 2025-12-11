import json

from langchain.messages import HumanMessage, SystemMessage
import os
from langchain_openai import AzureChatOpenAI
from scripts.utils import strip_code_fence, json_fix

from intelligent_reporting.agents.fallback_manager import get_fallback_llm


def assistant_query(
    supervisor_response: list[dict], path: str, offline_mode: bool = False
):
    """
    Docstring for assistant_query

    :param supervisor_response: Description
    :type supervisor_response: list[dict]
    :param path: Description
    :type path: str
    :param model: Description
    :type model: str
    :param offline_mode: Description
    :type offline_mode: bool
    """
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
Supervisor plan: {json.dumps(supervisor_response)}
Dataset path: {path}
Return ONLY a task name on the first line and Python code starting on the second line.
                """
            )
        ),
    ]

    try:
        response = llm.invoke(llm_prompt)
        content = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )
        raw = strip_code_fence(content)
        fixed = json_fix(raw)
        if not isinstance(fixed, str):

            fixed = json.dumps(fixed)

        name, code = fixed.split("\n", 1)
        name = name.strip()
        code = code.strip()

        return {"name": name, "code": code}

    except Exception as e:
        print(Exception(f"Failed to generate Python code: {str(e)}"))
        llm = get_fallback_llm(task_type="text")
        response = llm.invoke(llm_prompt)
        content = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )
        raw = strip_code_fence(content)
        raw = strip_code_fence(response.content)
        fixed = json_fix(raw)
        return fixed
