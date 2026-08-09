import os
import glob
import importlib

# Otomatis mendeteksi semua file .py di folder plugins/
files = glob.glob(os.path.join(os.path.dirname(__file__), "*.py"))
__all__ = [
    os.path.basename(f)[:-3]
    for f in files
    if os.path.isfile(f) and not f.endswith("__init__.py")
]

for plugin in __all__:
    importlib.import_module(f"plugins.{plugin}")
