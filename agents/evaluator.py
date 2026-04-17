from crewai import Agent

def create_evaluator():
    return Agent(
        role="Answer Evaluator",
        goal="Evaluate candidate answers",
        backstory="Senior engineer evaluating responses",
        llm = "ollama/qwen3:4b",
        verbose=True
    )