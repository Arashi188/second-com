import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

# Create the Flask app
app = create_app()

# Vercel handler
def handler(request, **kwargs):
    from flask import Request, Response
    from werkzeug.urls import url_decode
    
    # Convert Vercel request to WSGI
    environ = request.environ
    response = Response.from_app(app.wsgi_app, environ)
    return response