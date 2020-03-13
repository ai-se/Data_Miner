import pandas as pd

final = pd.DataFrame()
for i in range(100):
  #final = pd.DataFrame()
  try:
    df = pd.read_csv('Test_projects_' + str(i) + '.csv')
    #print(df.shape)
    final = pd.concat([final,df],axis = 0)
    if df[df['done']==1].shape[0] < 2:
      print("still working",i)
  except:
    print(i)
    continue
#print(final)
print(final.shape)
done_df = final[final['done'] == 1]
print(done_df.shape)
all_projects = pd.read_csv('suvodeep_understand.csv')
remaining_df = all_projects[~all_projects.repo_name.isin(done_df.repo_name)]
done_df.to_csv('done_projects_suvo.csv',index=False)
remaining_df.to_csv('remaining_projects_suvo.csv',index=False)
