#!/usr/bin/env python3
"""
Serve changelog content
"""
import os

def get_changelog():
    """Read and return changelog content"""
    changelog_path = os.path.join(os.path.dirname(__file__), 'CHANGELOG.md')
    try:
        with open(changelog_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "# Changelog\n\nNo changelog available."
