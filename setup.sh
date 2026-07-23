#!/bin/bash

conda init
conda activate thesis-env
conda install -c conda-forge llvm-openmp
conda install -c conda-forge python-kaleido
pip install -r requirements.txt
pipx install dolma
pipx ensurepath