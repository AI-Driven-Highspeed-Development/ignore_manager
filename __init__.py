# Add path handling to work from the new nested directory structure
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.getcwd()  # Use current working directory as project root
sys.path.insert(0, project_root)

from managers.ignore_manager.ignore_manager import IgnoreManager

__all__ = ["IgnoreManager"]
