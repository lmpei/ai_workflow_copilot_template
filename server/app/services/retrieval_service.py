def retrieve_context(workspace_id: str, question: str) -> list[str]:
    return [
        f"Workspace: {workspace_id}",
        f"Relevant context for question: {question}",
    ]


def generate_answer(question: str, context: list[str]) -> str:
    return f"Stub answer for '{question}'. Context items: {len(context)}"
