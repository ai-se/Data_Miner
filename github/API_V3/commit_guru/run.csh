#!/bin/tcsh
#BSUB -W 6000
#BSUB -n 2
#BSUB -R span[ptile=2]
#BSUB -o ./out/out.%J
#BSUB -e ./out/out.%J

module load python
python script.py

