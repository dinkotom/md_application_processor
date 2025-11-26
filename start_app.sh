#!/bin/bash

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to that directory
cd "$DIR"

# Open browser after a short delay (in background)
(sleep 2 && open http://localhost:5000) &

# Start the web app
python3 web_app.py

# Keep terminal open if there's an error
read -p "Press Enter to close..."
