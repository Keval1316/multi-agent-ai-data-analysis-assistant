import sys
import os

# Dynamically add project root to sys.path
_current_file = os.path.abspath(__file__)
_backend_dir = os.path.dirname(_current_file)
_project_root = os.path.dirname(_backend_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
