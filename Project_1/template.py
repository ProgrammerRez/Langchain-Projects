import os
from pathlib import Path

list_of_directories = ['demo.py',
                       'notebook/',
                       'app.py',
                       'main.py',
                       'state/state.py',
                       'state/__init__.py',
                       'prompts/prompts.py',
                       'exceptions/exceptions.py',
                       'logging/logging.py'
                       ]

if __name__=='__main__':
    for filepath in list_of_directories:
        filepath = Path(filepath)
        filedir, filename = os.path.split(filepath)
        if filedir != "":
            os.makedirs(filedir, exist_ok=True)
        if (not os.path.exists(filepath)) or (os.path.getsize(filepath) == 0):
            with open(filepath, "w") as f:
                pass
        else:
            print(f"file is already present at: {filepath}")