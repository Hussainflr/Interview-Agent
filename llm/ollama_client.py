import requests
import yaml

with open("config/settings.yaml") as f:
    config = yaml.safe_load(f)

MODEL = config["llm"]["model"]

def generate(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": config["app"]["temperature"]
            }
        }
    )
    return response.json()["response"]