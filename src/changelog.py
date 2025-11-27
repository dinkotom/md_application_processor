#!/usr/bin/env python3
"""
Serve changelog content
"""
import os

def get_changelog():
    """Read and return changelog content"""
    # Get the parent directory of src/ to find CHANGELOG.md
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    changelog_path = os.path.join(parent_dir, 'CHANGELOG.md')
    
    try:
        with open(changelog_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "# Changelog\n\nNo changelog available."
