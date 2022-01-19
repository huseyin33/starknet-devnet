#!/bin/bash

set -e

echo "Path before install:"
echo "$PATH"

pip3 install poetry
poetry config virtualenvs.create false
poetry install

echo "Path after install:"
echo "$PATH"
echo "Starknet version:"
starknet --version 
