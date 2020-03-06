#!/bin/sh
#SBATCH -p max -N 1 -w c[23]
python compute.py
