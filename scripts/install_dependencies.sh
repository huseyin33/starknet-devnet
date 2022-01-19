#!/bin/bash

set -e

pip3 install poetry
poetry config virtualenvs.create false
poetry install

echo "Starknet version:"
starknet --version 