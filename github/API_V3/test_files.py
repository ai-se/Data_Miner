from __future__ import division
from api import git_access,api_access
from git_understand import git_understand
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
from commit_guru.cas_manager import *

if __name__ == "__main__":
    if platform.system() == 'Darwin' or platform.system() == 'Linux':
        data_path = os.getcwd() + '/Test_projects.csv'
    else:
        data_path = os.getcwd() + '\\Test_projects.csv'
    code_path = os.getcwd()
    project_list = pd.read_csv(data_path)
    for i in range(project_list.shape[0]):
        try:
            print("I am here")
            #understand_source = []
            #last_analyzed = None
            #access_token = project_list.loc[i,'access_token']
            #repo_owner = project_list.loc[i,'repo_owner']
            #source_type = project_list.loc[i,'source_type']
            #git_url = project_list.loc[i,'git_url']
            #api_base_url = project_list.loc[i,'api_base_url']
            #repo_name = project_list.loc[i,'repo_name']
            #repo_lang = project_list.loc[i,'lang']
            #understand_source.append([1,repo_name,git_url,last_analyzed])
            #understand_source_df = pd.DataFrame(understand_source,columns = ['id','name','url','last_analyzed'])
            #cas_manager = CAS_Manager(understand_source_df)
            #cas_manager.start()
            #git_data = git2data.git2data(access_token,repo_owner,source_type,git_url,api_base_url,repo_name)
            ##git_data = release_mine.git2data(access_token,repo_owner,source_type,git_url,api_base_url,repo_name)
            #git_data.create_data()
            #os.chdir(code_path)
            df_commit = pd.read_pickle(up(code_path) + '/data/commit/' + repo_name + '_commit.pkl')
            df_commit_guru = pd.read_csv(up(code_path) + '/data/commit_guru/' + repo_name + '.csv')
            df_commit_guru_subset = df_commit_guru[['commit_hash','contains_bug']].fillna(False)
            df = pd.merge(df_commit,df_commit_guru_subset, on='commit_hash',how='inner')
            df.to_pickle(up(code_path) + '/data/commit/' + repo_name + '_commit.pkl')
            get_matrix = git_understand.MetricsGetter(git_url,repo_name,repo_lang)
            matrix = get_matrix.get_defective_pair_metrics()
        except ValueError as e:
            print("Exception occured for ",project_list.loc[i,'git_url'])
            print(e)
            continue
        # df = pd.read_pickle('C:/Users/prana/Desktop/AI-SE_RA_Repo/Data_Miner/github/data/release/github-plugin_release.pkl')
        # print(df)
