#!/bin/sh
#SBATCH -p max -N 1 -w c[26]
python commit_mine.py
