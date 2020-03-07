#!/bin/sh
#SBATCH -p max -N 1 -w c[27]
python compute.py
