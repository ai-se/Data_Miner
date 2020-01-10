#!/bin/tcsh
#BSUB -W 6000
#BSUB -n 8
#BSUB -R span[ptile=8]
#BSUB -o stdout.%J
#BSUB -e stderr.%J

module load python
python new.py