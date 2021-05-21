#!/bin/bash

python3 -m coverage run --source speach --branch -m unittest discover -s test
python3 -m coverage html

