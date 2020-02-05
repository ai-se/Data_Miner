#!/bin/sh
#SBATCH -p max -N 1 -w c[23] --pty /bin/bash
python run.py
