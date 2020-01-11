import understand as und
import numpy
from git_understand import git_understand
from api import git_access,api_access
from git_understand import git_understand_v1 as git_understand
from git_log import git2repo
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import networkx as nx
import re
from git_log import git2data,git_commit_info,release_mine
import threading
from threading import Barrier
from multiprocessing import Queue
from os.path import dirname as up
import os
import platform
from commit_guru.cas_manager_v1 import *

print("its working")
# df = pd.DataFrame([1,2,3,4,5,6,7,8,9,10])
# df.to_csv('data.csv')

if __name__ == "__main__":
  if platform.system() == 'Darwin' or platform.system() == 'Linux':
    data_path = os.getcwd() + '/Test_projects.csv'
  else:
    data_path = os.getcwd() + '\\Test_projects.csv'
    code_path = os.getcwd()
  project_list = pd.read_csv(data_path)
  code_path = os.getcwd()
  print(project_list)
  for i in range(project_list.shape[0]):
    try:
      print("I am here")
      understand_source = []
      last_analyzed = None
      access_token = project_list.loc[i,'access_token']
      repo_owner = project_list.loc[i,'repo_owner']
      source_type = project_list.loc[i,'source_type']
      git_url = project_list.loc[i,'git_url']
      api_base_url = project_list.loc[i,'api_base_url']
      repo_name = project_list.loc[i,'repo_name']
      repo_lang = project_list.loc[i,'lang']
      understand_source.append([1,repo_name,git_url,last_analyzed])
      understand_source_df = pd.DataFrame(understand_source,columns = ['id','name','url','last_analyzed'])
      cas_manager = CAS_Manager(understand_source_df)
      cas_manager.start()
      os.chdir(code_path)
      get_matrix = git_understand.MetricsGetter(git_url,repo_name,repo_lang)
      matrix = get_matrix.get_defective_pair_metrics()
    except ValueError as e:
      print("error",e)
      continue

# df = pd.DataFrame([1,2,3,4,5,6,7,8,9,10,11,12])
# df.to_csv('data.csv')
