#!/bin/sh
#SBATCH -p max -N 1 -w c[31]
python commit_mine.py
