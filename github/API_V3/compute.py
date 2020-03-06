import understand as und
import numpy
from api import git_access,api_access
from git_understand import compute_metrics_final as compute_metrics_final
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



def compute(projects,code_path,core):
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
      os.chdir(code_path)
      get_matrix = compute_metrics_final.MetricsGetter(git_url,repo_name,repo_lang,code_path)
      matrix = get_matrix.get_defective_pair_metrics()
      project_list.loc[i,'done'] = 1
      project_list.to_csv('completed_projects_' + str(core) + '.csv')
      print(project_list)
      print('Done')
    except ValueError as e:
      print("error",e)
      continue

if __name__ == "__main__":
  if platform.system() == 'Darwin' or platform.system() == 'Linux':
    data_path = os.getcwd() + '/ken.csv'
  else:
    data_path = os.getcwd() + '\\Test_projects.csv'
    code_path = os.getcwd()
  project_list = pd.read_csv(data_path)
  # project_list = project_list[project_list['lang'] == 'Python']
  #project_list = project_list[0:4]
  # miner = data_mine(project_list)
  # miner.start()
  code_path = os.getcwd()
  cores = cpu_count()
  threads = []
  projects = np.array_split(project_list.index.tolist(), 100)
  for i in range(len(projects)):
    _sub_group = project_list.loc[list(projects[i])]
    _sub_group.reset_index(inplace = True, drop = True)
    print(_sub_group)
    t = ThreadWithReturnValue(target = compute, args = [_sub_group,code_path,i])
    # t = ThreadWithReturnValue(target = check, args = [i])
    threads.append(t)
  for th in threads:
    th.start()
  for th in threads:
    response = th.join()
