from crewai import Crew, Task
from agents import interviewer
from agents.interviewer import create_interviewer
from agents.evaluator import create_evaluator
from llm.ollama_client import generate_streaming_response
from crewai.llm import LLM

    
def build_crew():

    llm = LLM(
        model="ollama/qwen3:4b",   # ✅ native support
        temperature=0.7
    )
    interviewer = create_interviewer()
    evaluator = create_evaluator()

    task = Task(
    description="Ask a technical interview question based on the candidate's previous answer and evaluate their response",
    expected_output="""
    1. A clear and concise follow-up interview question
    2. Evaluation of the candidate's answer (strengths, weaknesses)
    3. Suggestions for improvement
    """,
    agent=interviewer
)

    return Crew(
        agents=[interviewer, evaluator],
        tasks=[task],
        verbose=True
    )