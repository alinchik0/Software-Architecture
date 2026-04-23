PLANNER_PROMPT = """Break the question into 3-5 clear subtasks.
Return JSON: {"subtasks": []}"""

WORKER_PROMPT = """Answer the subtask clearly and concisely."""

AGGREGATOR_PROMPT = """Combine the following into a structured, coherent answer:"""

CRITIC_PROMPT = """Find problems in the answer.
Return JSON: {"issues": []}"""

REFINER_PROMPT = """Improve the answer based on the issues."""

JUDGE_PROMPT = """Decide if the answer is good enough.
Return JSON: {"verdict": "accept" or "retry"}"""