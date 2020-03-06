import pandas as pd

df = pd.DataFrame()
for i in range(50):
	#df = pd.DataFrame()
	try:
		_df = pd.read_csv('Test_projects_' + str(i)  + '.csv')
		df = pd.concat([df,_df],axis = 0)
		print(i,_df.shape)
		print(i,_df[_df['done'] == 1].shape)
	except:
		print(i)
		continue
print("+++++++++++++++++++++++++++++")
print(df.shape)
_df_1 = df[df['done'] == 1]
print(_df_1.shape)
_df_1.to_csv('done_projects_ken.csv')
