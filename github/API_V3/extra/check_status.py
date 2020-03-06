import pandas as pd

final = pd.DataFrame()
for i in range(100):
  #final = pd.DataFrame()
  try:
    df = pd.read_csv('Test_projects_' + str(i) + '.csv')
    final = pd.concat([final,df],axis = 0)
    if df[df['done']==1].shape[0] < 2:
      print("still working",i)
  except:
    print(i)
    continue
print(final)
print(final.shape)
remaining_df = final[final['done'] == 1]
print(remaining_df)
remaining_df.to_csv('done_projects_suvo.csv')
