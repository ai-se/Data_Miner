from __future__ import division
from api import git_access,api_access
from git_log import git2repo
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import networkx as nx
import re
from git_log import git2data,git_commit_info
import threading
from threading import Barrier
from multiprocessing import Queue
from os.path import dirname as up
import os
import platform

if __name__ == "__main__":
    if platform.system() == 'Darwin' or platform.system() == 'Linux':
        data_path = os.getcwd() + '/Test_projects.csv'
    else:
        data_path = os.getcwd() + '\\Test_projects.csv'
    project_list = pd.read_csv(data_path)
    for i in range(project_list.shape[0]):
        try:
            print("I am here")
            print(project_list)
            access_token = project_list.loc[i, 'access_token']
            repo_owner = project_list.loc[i, 'repo_owner']
            source_type = project_list.loc[i, 'source_type']
            git_url = project_list.loc[i, 'git_url']
            api_base_url = project_list.loc[i, 'api_base_url']
            repo_name = project_list.loc[i, 'repo_name']
            # git_data = git2data.git2data(access_token,repo_owner,source_type,git_url,api_base_url,repo_name)
            git_data = git_commit_info.git2data(access_token, repo_owner, source_type, git_url, api_base_url, repo_name)
            print(git_data, type(git_data))
            git_data.create_data()
        except ValueError as e:
            print("Exception occured for ", project_list.loc[i, 'git_url'])
            print(e)
    df = pd.read_pickle('C:/Users/prana/Desktop/AI-SE_RA_Repo/Data_Miner/github/data/release/github-plugin_release.pkl')
    print(df)
