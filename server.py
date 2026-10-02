"""Root directory launcher for AgroIntelli.

Automatically redirects execution to the inner project directory (Agrointelli-main)
so running 'python server.py' from either D:\\Agrointelli-main or
D:\\Agrointelli-main\\Agrointelli-main works seamlessly.
"""

import os
import sys

# Set working directory to the inner Agrointelli-main folder
base_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(base_dir, "Agrointelli-main")

if os.path.exists(project_dir):
    os.chdir(project_dir)
    sys.path.insert(0, project_dir)

# Import and launch server
import server
import uvicorn

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  AgroIntelli AI & Bilingual AgroBot Server Running")
    print("  - Localhost: http://localhost:8000")
    print("  - Local Network: http://0.0.0.0:8000")
    print("=" * 55 + "\n")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
