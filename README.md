# Ignore Manager

## Overview

Programmatically manage `.gitignore` entries within a **private managed zone**. 

This manager ONLY operates within a marked zone in `.gitignore` and **never touches entries outside the zone**, even if duplicates exist. This ensures user's manual entries are always preserved.

## The Managed Zone

The manager creates and maintains a clearly marked zone:

```gitignore
# User's manual entries above are untouched
*.pyc
__pycache__/

# ========== ADHD MANAGED v1 - DO NOT EDIT ==========
project/data/secrets.yaml
project/data/secrets.*.yaml
# ========== END ADHD MANAGED ==========
```

**Key behaviors:**
- Zone is created at the **end** of `.gitignore` if it doesn't exist
- Entries are ONLY added/removed within the zone
- User entries outside the zone are **never modified**
- Duplicate entries (one inside, one outside) are allowed - we only manage ours

## Features

- **ensure_ignored(path)** - Adds path to zone if not present
- **is_ignored(path)** - Checks if path is in the managed zone
- **is_globally_ignored(path)** - Checks if path exists anywhere in `.gitignore`
- **add_ignore_pattern(pattern)** - Adds glob patterns (e.g., `*.log`)
- **remove_entry(path)** - Removes entry from zone only
- **list_entries()** - Lists entries in the managed zone
- **ensure_multiple(paths)** - Batch add multiple paths
- Creates `.gitignore` if it doesn't exist
- Handles corrupted zones gracefully (recreates if malformed)

## Usage

```python
from managers.ignore_manager import IgnoreManager

# Default: operates on project root .gitignore
ignore = IgnoreManager()

# Ensure a file is ignored (adds to managed zone)
ignore.ensure_ignored("project/data/secrets.yaml")

# Ensure patterns are ignored
ignore.add_ignore_pattern("*.log")
ignore.add_ignore_pattern("project/data/secrets.*.yaml")

# Check if in our managed zone
if ignore.is_ignored("project/data/secrets.yaml"):
    print("In managed zone!")

# Check if ignored anywhere in .gitignore
if ignore.is_globally_ignored("*.pyc"):
    print("Ignored somewhere (maybe user added it)")

# Batch operations
ignore.ensure_multiple([
    "project/data/secrets.yaml",
    "project/data/local.config",
    ".env"
])

# List only our managed entries
for entry in ignore.list_entries():
    print(entry)

# Custom .gitignore path
custom_ignore = IgnoreManager(gitignore_path="/path/to/.gitignore")
```

## Module Structure

```
managers/ignore_manager/
├── __init__.py          # Module exports
├── init.yaml            # Module metadata
├── ignore_manager.py    # IgnoreManager class
└── README.md            # This file
```

## Dependencies

- `logger_util` - For logging operations