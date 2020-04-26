import pandas as pd

df = pd.read_csv('projects.csv')
df['done'] = [0]*df.shape[0]
for i in range(df.shape[0]):
    try:
        _df = pd.read_csv('/home/smajumd3/Data_Miner/github/data/commit_guru_new/' + df.loc[i,'repo_name'] + '_file.csv' )
        df.loc[i,'done'] = 1
    except:
        continue
df = df[df['done'] == 0]
df.to_csv('projects_new.csv',index = False)