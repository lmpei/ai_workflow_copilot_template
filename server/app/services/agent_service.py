from app.agents.graph import run_agent


def run_agent_preview(goal: str) -> dict:
    return run_agent(goal=goal)
