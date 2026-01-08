from pathlib import Path
import os


list_of_dir = ['/state/__init__.py',
               '/logger/__init__.py',
               '/exceptions/__init__.py',
               '/notebooks/prototyping.ipynb',
               '/tests/basic_test.py',
               'main.py',
               'app.py',
               'demo.py']


for dir in list_of_dir:
    path = Path(dir)

    file_path, filename = os.path.split(path)
    
    if not os.path.exists(file_path):
    os.makedirs(file_path,exist_ok=True)
    