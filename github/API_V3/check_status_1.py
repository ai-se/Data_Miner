import pandas as pd
from os import path

df = pd.read_csv('Test_projects.csv')
for i in range(df.shape[0]):
	project_name = df.loc[i,'repo_name']
	folder_path = '/tmp/hqtu/temp/udb/' + project_name
	if path.exists(folder_path):
		df.loc[i,'done'] = 1
df.to_csv('all.csv')
print(df[df['done']==1].shape)
