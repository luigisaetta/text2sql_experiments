# utility to format ancd check quality of code
black *.py

PYTHONPATH=. pylint  --disable=R0801  *.py

