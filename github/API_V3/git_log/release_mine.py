# -*- coding: utf-8 -*-
"""
Created on Thu Aug 30 10:30:28 2018

@author: suvod
"""
from __future__ import division
import sys
sys.path.append("..")
from api import git_access,api_access
from git_log import git2repo,buggy_commit
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import os
import re
import networkx as nx
import platform
from os.path import dirname as up
import datetime

class git2data(object):
    
    def __init__(self,access_token,repo_owner,source_type,git_url,api_base_url,repo_name):
        self.repo_name = repo_name
        if platform.system() == 'Darwin' or platform.system() == 'Linux':
            self.data_path = up(os.getcwd()) + '/data/'
        else:
            self.data_path = up(os.getcwd()) + '\\data\\'
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
        self.git_client = api_access.git_api_access(access_token,repo_owner,source_type,git_url,api_base_url,repo_name)
        self.git_repo = git2repo.git2repo(git_url,repo_name)
        #self.repo = self.git_repo.clone_repo()
        
    def get_api_data(self):
        # self.git_issues = self.git_client.get_issues(url_type = 'issues',url_details = '')
        self.git_releases = self.git_client.get_tagged_release(url_type = 'tags',url_details = '')
        # self.git_issue_events = self.git_client.get_events(url_type = 'issues',url_details = 'events')
        # self.git_issue_comments = self.git_client.get_comments(url_type = 'issues',url_details = 'comments')
        # self.user_map = self.git_client.get_users()
    
    def create_data(self,get_api_data=True,get_commit_data=False,get_all_branch=True):
        if get_api_data:
            self.get_api_data()
        
        release_df = pd.DataFrame(self.git_releases, columns = ['Release_id','author_logon','tag','created_at','description'])
        release_df.to_pickle(self.data_path + '/release/' + self.repo_name + '_release.pkl')
        #self.git_repo.repo_remove()
        #print(self.repo_name,"Repo Done")
        return release_df.shape[0]