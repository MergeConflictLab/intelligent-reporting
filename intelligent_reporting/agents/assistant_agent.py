import json
import os
from langchain.messages import HumanMessage, SystemMessage
from scripts.utils import strip_code_fence, json_fix

from .fallback_manager import get_fallback_llm
from .base_agent import Agent


class AssistantAgent(Agent):
    """
    Agent responsible for generating Python code.
    """

    def run(
        self, supervisor_response: dict, path: str, offline_mode: bool = False
    ):
        """
        Generate Python code based on the supervisor's plan.
        """
        print(
            f"[{self.__class__.__name__}] Starting execution for task: {supervisor_response.get('name', 'unknown')}..."
        )
        if offline_mode:
            llm = get_fallback_llm(task_type="code")
        else:
            from langchain_openai import AzureChatOpenAI

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

RULES:
- Only use pandas, numpy, matplotlib, seaborn, plotly.
- Load the dataset into df from the given path.
- If randomness: np.random.seed(42).
- Use plt.savefig(), never plt.show().
- No file I/O except saving plots.
- Use only columns mentioned by the supervisor; skip missing ones.

DEFENSIVE CODING (CRITICAL):
- ALWAYS convert columns to numeric with pd.to_numeric(col, errors='coerce') before math operations.
- ALWAYS drop NaN values with .dropna() before plotting or aggregating.
- NEVER use .pivot() without handling duplicates first. Use .pivot_table(aggfunc='mean') instead.
- NEVER assign vectors of different lengths to the dataframe. Create new variables instead.
- When grouping, always use .reset_index() to avoid index issues.
- Wrap column access in try/except or check if column exists with 'if col in df.columns'.
- Use .copy() when subsetting DataFrames to avoid SettingWithCopyWarning.
- For bar plots with categorical x-axis, convert to string: df['col'] = df['col'].astype(str).
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

            if "\n" in fixed:
                name, code = fixed.split("\n", 1)
            else:
                name = "generated_task"
                code = fixed

            name = name.strip()
            code = code.strip()

            print(f"[{self.__class__.__name__}] Code generation successful.")
            print(f"[{self.__class__.__name__}] Generated Code:\n{code}")
            return {"name": name, "code": code}

        except Exception as e:
            print(
                f"[{self.__class__.__name__}] Error: {str(e)}. Switching to fallback..."
            )
            print(f"Failed to generate Python code: {str(e)}")

            llm = get_fallback_llm(task_type="text")
            response = llm.invoke(llm_prompt)
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            raw = strip_code_fence(content)

            if "\n" in raw:
                name, code = raw.split("\n", 1)
            else:
                name = "fallback_task"
                code = raw

            return {"name": name.strip(), "code": code.strip()}
