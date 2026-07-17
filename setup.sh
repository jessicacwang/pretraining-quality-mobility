#!/bin/bash

conda init
conda activate thesis-env
pip install -r requirements.txt
pipx install dolma
pipx ensurepath