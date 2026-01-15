"""
JSON Utilities for Task Health Monitor
Functions to save and load JSON data files.
"""
import json
import os


def save_json(data, filename, directory='data'):
    """
    Save data to JSON file with timestamp.

    Args:
        data: Data to save
        filename: Name of the file
        directory: Directory to save in (default: 'data')

    Returns:
        str: Full path to saved file
    """
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)

    print(f"✓ Saved: {filepath}")
    return filepath


def load_json(filepath):
    """
    Load data from JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        dict: Loaded data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
