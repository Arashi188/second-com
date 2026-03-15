# api/index.py
from app import create_app
import os
import sys

# Add the parent directory to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = create_app()

# This is for Vercel serverless function
def handler(request):
    return app(request)