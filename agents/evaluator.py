from crewai import Agent

def create_evaluator(llm):
    return Agent(
        role="Answer Evaluator",
        goal="Evaluate candidate answers",
        backstory="Senior engineer evaluating responses",
        llm=llm,
        verbose=True
    )