#!/usr/bin/env python3
"""
Vantage Launcher - Redirects to the new Vantage location
"""
import os
import sys
import subprocess

def main():
    # Path to the Vantage main.py (in the current directory's app folder)
    new_vantage_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        'app', 'main.py'
    ))
    
    if not os.path.exists(new_vantage_path):
        print(f"Error: Could not find Vantage at {new_vantage_path}")
        sys.exit(1)
    
    # Run the new Vantage
    cmd = [sys.executable, new_vantage_path] + sys.argv[1:]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error launching Vantage: {e}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
