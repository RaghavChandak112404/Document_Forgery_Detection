import sys
import os

# Add backend directory to sys.path to resolve imports
backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.append(backend_path)

# Import the FastAPI instance from backend/main.py at the top level
# so Vercel can statically analyze and find the 'app' variable.
from main import app
