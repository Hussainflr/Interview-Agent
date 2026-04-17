from crewai import Agent

def create_interviewer():
    return Agent(
        role="Technical Interviewer",
        goal="Ask structured interview questions",
        backstory="Expert interviewer in software engineering",
        llm = "ollama/qwen3:4b",
        verbose=True
    )