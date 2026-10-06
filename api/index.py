import os
import sys

# Ensure root directory is on the Python module search path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wsgi import app, application

# Expose WSGI application for Vercel Serverless Function
if __name__ == "__main__":
    app.run()
