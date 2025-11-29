#!/bin/bash

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to that directory
cd "$DIR"

# Install dependencies
echo "Checking dependencies..."
pip3 install -r requirements.txt > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Warning: Failed to install dependencies. Trying to continue..."
fi

# Open browser after a short delay (in background)
(sleep 2 && open http://localhost:5000) &

# Start the web app
python3 web_app.py

# Keep terminal open if there's an error
read -p "Press Enter to close..."
