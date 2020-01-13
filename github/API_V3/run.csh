#!/bin/tcsh
#BSUB -W 6000
#BSUB -n 8
#BSUB -R span[ptile=8]
#BSUB -o stdout.%J
#BSUB -e stderr.%J

module load python
module load und

und create -languages Java add /gpfs_common/share02/tjmenzie/smajumd3/AI4SE/Data_Miner/github/API_V3/commit_guru/ingester/CASRepos/git/Android-ObservableScrollView analyze /gpfs_common/share02/tjmenzie/smajumd3/AI4SE/Data_Miner/github/API_V3/.temp/udb/Android-ObservableScrollView_clean.udb

#python new.py