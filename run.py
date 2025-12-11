"""Simple script to run the MeetingMiner Flask API server."""
import subprocess
import sys
import os

if __name__ == "__main__":
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run Flask app
    subprocess.run([sys.executable, "api.py"])


