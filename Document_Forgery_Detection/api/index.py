import sys
import os

# Create a bridge between Vercel and the FastAPI backend
# This allows the backend to be served as a serverless function

# Add backend directory to sys.path to resolve imports
backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.append(backend_path)

# Import the FastAPI instance from backend/main.py
from main import app

# Vercel needs the app object to be available as 'app'
# This is already handled by the import above
