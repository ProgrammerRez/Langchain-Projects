from pathlib import Path
import os

# -------------------------
# PROJECT STRUCTURE
# -------------------------
PROJECT_STRUCTURE = [
    # Core app
    "app.py",                  # FastAPI entrypoint
    "main.py",                 # CLI / local runner
    "demo.py",                 # End-to-end demo flow

    # Agent logic
    "agents/__init__.py",
    "agents/router.py",        # decide: answer / escalate / request_info
    "agents/responder.py",     # LLM answer generation
    "agents/escalation.py",    # human handoff logic

    # State management
    "state/__init__.py",
    "state/ticket_state.py",   # conversation + SLA state
    "state/memory.py",         # past tickets / history

    # Knowledge
    "knowledge/__init__.py",
    "knowledge/kb_loader.py",  # load docs / FAQs
    "knowledge/retriever.py",  # vector search over KB + tickets

    # Decision logic
    "decision/__init__.py",
    "decision/policy.py",      # escalation rules, confidence thresholds
    "decision/confidence.py",  # scoring + guardrails

    # Integrations
    "integrations/__init__.py",
    "integrations/zendesk.py",
    "integrations/intercom.py",

    # Observability
    "logger/__init__.py",

    # Errors
    "exceptions/__init__.py",

    # Tests
    "tests/__init__.py",
    "tests/test_router.py",
    "tests/test_confidence.py",

    # Notebooks
    "notebooks/prototyping.ipynb",
]

# -------------------------
# CREATE FILES & DIRS
# -------------------------
def create_project_structure():
    for item in PROJECT_STRUCTURE:
        path = Path(item)
        dir_path = path.parent

        if dir_path != Path("."):
            os.makedirs(dir_path, exist_ok=True)

        if not path.exists():
            path.touch()

    print("✅ Customer Support Resolution Agent scaffold created")


if __name__ == "__main__":
    create_project_structure()
