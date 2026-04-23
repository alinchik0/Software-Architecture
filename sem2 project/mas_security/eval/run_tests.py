from agents.graph import graph

test_questions = [
    # Простые
    "What is gravity?",
    "Explain photosynthesis simply",

    # Средние
    "How does blockchain work?",
    "What are the causes of World War 1?",

    # Сложные
    "Compare capitalism and socialism with examples",
    "Explain quantum computing and its challenges",

    # Логика
    "Why do airplanes fly?",
    "What happens if the sun disappears?",

    # С подвохом
    "Is time travel possible?",
    "Can AI become conscious?"
]


def run_tests():
    for i, q in enumerate(test_questions):
        print("\n" + "=" * 60)
        print(f"TEST {i+1}: {q}")

        state = {
            "question": q,
            "subtasks": [],
            "worker_outputs": [],
            "draft_answer": "",
            "critique": "",
            "final_answer": "",
            "iteration": 0
        }

        result = graph.invoke(state)

        print("\nFINAL ANSWER:\n")
        print(result["final_answer"])
        print("\nITERATIONS:", result["iteration"])


if __name__ == "__main__":
    run_tests()