from crewai import Agent

def create_interviewer(llm):
    return Agent(
        role="Technical Interviewer",
        goal="Ask structured interview questions",
        backstory="Expert interviewer in software engineering",
        llm=llm,
        verbose=True
    )