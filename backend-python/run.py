"""Start the Python backend: python backend-python/run.py  (env: HOST, PORT)."""
import os

from taskboard import create_app

if __name__ == "__main__":
    create_app().run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
    )
