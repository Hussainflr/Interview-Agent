from crewai import Crew, Task
from agents.interviewer import create_interviewer
from agents.evaluator import create_evaluator
from llm.ollama_client import generate

class LLMWrapper:
    def call(self, prompt):
        return generate(prompt)

def build_crew():
    llm = LLMWrapper()

    interviewer = create_interviewer(llm)
    evaluator = create_evaluator(llm)

    task = Task(
        description="Conduct interview and evaluate answers",
        agent=interviewer
    )

    return Crew(
        agents=[interviewer, evaluator],
        tasks=[task],
        verbose=True
    )