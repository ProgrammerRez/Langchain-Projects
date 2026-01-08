import os
from pathlib import Path

list_of_directories = ['logger/__init__.py',
                       'exceptions/__init__.py',
                       'prompts/__init__.py',
                       'state/__init__.py',
                       'steps/File_Classification.py',
                       'steps/Validation.py',
                       'steps/Pipeline.py',
                       'steps/Routing.py',
                       'steps/__init__.py',
                       'app.py',
                       'requirements.txt',
                       'README.md',
                       'notebook/Prototyping.ipynb'
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