import understand as und
import numpy
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
from threading import Thread
import numpy as np
import itertools
import pandas as pd
import sys
import shutil,os
from git_log import git2repo
import os
import re
import shlex
from multiprocessing import Pool, cpu_count
from os.path import dirname as up
from commit_guru.cas_manager_v1 import *
import subprocess as sp

class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
    def run(self):
        #print(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return



def mine(projects,code_path):
  for i in range(projects.shape[0]):
    try:
      print("I am here")
      understand_source = []
      last_analyzed = None
      access_token = projects.loc[i,'access_token']
      repo_owner = projects.loc[i,'repo_owner']
      source_type = projects.loc[i,'source_type']
      git_url = projects.loc[i,'git_url']
      api_base_url = projects.loc[i,'api_base_url']
      repo_name = projects.loc[i,'repo_name']
      repo_lang = projects.loc[i,'lang']
      understand_source.append([1,repo_name,git_url,last_analyzed])
      understand_source_df = pd.DataFrame(understand_source,columns = ['id','name','url','last_analyzed'])
      file_path = up(code_path) + '/data/commit_guru/' + repo_name + '.csv'
      cas_manager = CAS_Manager(understand_source_df)
      if os.path.isfile(file_path):
        print('file exist')
        cas_manager.run_ingestion()
      else:
        cas_manager.run()
      os.chdir(code_path)
      print(code_path)
      get_matrix = git_understand.MetricsGetter(git_url,repo_name,repo_lang,code_path)
      matrix = get_matrix.get_defective_pair_udb_files()
      print('Done')
    except ValueError as e:
      print("error",e)
      continue

if __name__ == "__main__":
  if platform.system() == 'Darwin' or platform.system() == 'Linux':
    data_path = os.getcwd() + '/Test_projects.csv'
  else:
    data_path = os.getcwd() + '\\Test_projects.csv'
    code_path = os.getcwd()
  project_list = pd.read_csv(data_path)
  project_list = project_list[project_list['lang'] == 'Python']
  #project_list = project_list[0:1]
  # miner = data_mine(project_list)
  # miner.start()
  code_path = os.getcwd()
  cores = cpu_count()
  threads = []
  print(cores)
  projects = np.array_split(project_list.index.tolist(), cores)
  for i in range(len(projects)):
    _sub_group = project_list.loc[list(projects[i])]
    _sub_group.reset_index(inplace = True, drop = True)
    print(_sub_group)
    t = ThreadWithReturnValue(target = mine, args = [_sub_group,code_path])
    # t = ThreadWithReturnValue(target = check, args = [i])
    threads.append(t)
  for th in threads:
    th.start()
  for th in threads:
    response = th.join()

