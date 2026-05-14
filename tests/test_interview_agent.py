from agents.interview_agent import classify_intent, heuristic_evaluation


def test_greeting_does_not_trigger_interview_pipeline():
    result = classify_intent("hello")
    assert result["intent"] == "greeting"


def test_short_unclear_answer_is_not_scored():
    result = classify_intent("not sure")
    assert result["intent"] == "unclear"


def test_real_answer_is_routed_for_scoring():
    text = "I would first clarify the requirements, then design a small prototype, test it with users, and measure the result."
    result = classify_intent(text)
    assert result["intent"] == "interview_answer"


def test_heuristic_evaluation_has_expected_shape():
    result = heuristic_evaluation("I used a structured approach because the project had risk, and the result improved delivery.")
    assert 0 <= result["score"] <= 100
    assert set(result["rubric"]) == {"relevance", "clarity", "depth", "structure", "role_fit"}
    assert result["follow_up_question"]

