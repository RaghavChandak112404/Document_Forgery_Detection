import sys
import os

# Create a bridge between Vercel and the FastAPI backend
# This allows the backend to be served as a serverless function

try:
    # Add backend directory to sys.path to resolve imports
    backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
    sys.path.append(backend_path)
    print(f"DEBUG: sys.path augmented with: {backend_path}")

    # Import the FastAPI instance from backend/main.py
    from main import app
    print("DEBUG: Successfully imported 'app' from 'main'")
except Exception as e:
    print(f"ERROR during initialization: {e}")
    import traceback
    traceback.print_exc()
    raise e
