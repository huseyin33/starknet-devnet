#!/bin/bash

set -e

echo "python path:"
which python
echo "python3 path:"
which python3

pip3 install poetry
echo "poetry show before:"
poetry show -v
poetry config virtualenvs.create false
echo "poetry show after:"
poetry show -v

poetry install

echo "Starknet version:"
starknet --version 
