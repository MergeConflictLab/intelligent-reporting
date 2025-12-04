from toon_format import encode, decode
from langchain.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama


def assistant_query(supervisor_response, path, model="mistral"):
    llm = ChatOllama(model=model, temperature=0.1)

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
                Supervisor plan: {encode(supervisor_response)}
                Dataset path: {path}
                Return ONLY a task name on the first line and Python code starting on the second line.
                """
            )
        ),
    ]

    try:
        response = llm.invoke(llm_prompt)
        raw = response.content.strip()

        name, code = raw.split("\n", 1)
        name = name.strip()
        code = code.strip()

        return {"name": name, "code": code}

    except Exception as e:
        raise e
