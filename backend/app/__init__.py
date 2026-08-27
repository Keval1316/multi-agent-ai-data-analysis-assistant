import sys
import os

# Dynamically add project root and backend dir to sys.path
_current_file = os.path.abspath(__file__)
_app_dir = os.path.dirname(_current_file)
_backend_dir = os.path.dirname(_app_dir)
_project_root = os.path.dirname(_backend_dir)
for _p in [_project_root, _backend_dir]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
