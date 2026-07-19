#!/bin/bash

conda init
conda activate thesis-env
conda install -c conda-forge llvm-openmp
pip install -r requirements.txt
pipx install dolma
pipx ensurepath