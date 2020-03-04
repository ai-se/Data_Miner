#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append("..")
from pygit2 import clone_repository
from pygit2 import GIT_SORT_TOPOLOGICAL, GIT_SORT_REVERSE,GIT_MERGE_ANALYSIS_UP_TO_DATE,GIT_MERGE_ANALYSIS_FASTFORWARD,GIT_MERGE_ANALYSIS_NORMAL,GIT_RESET_HARD
from pygit2 import Repository
import shutil,os
import pygit2
from git_log import git2repo
import os
import re
import shlex
import numpy as np
import pandas as pd
from glob2 import glob, iglob
import subprocess as sp
import understand as und
from pathlib import Path
from pdb import set_trace
import sys
from collections import defaultdict
from utils.utils import utils
import platform
from os.path import dirname as up
from multiprocessing import Pool, cpu_count
import threading
from multiprocessing import Queue
from threading import Thread
import random
import string
#from main.utils.utils.utils import printProgressBar

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


class MetricsGetter(object):
    """
    Generate class, file, function, object oriented metrics for a project.

    Parameters
    ----------
    sources_path: str or pathlib.PosixPath

    Notes
    -----
    The class is designed to run in conjunction with a context manager.
    """

    def __init__(self,repo_url,repo_name,repo_lang,code_path):
        self.repo_url = repo_url
        self.repo_name = repo_name
        self.repo_lang = repo_lang
        #self.repo_obj = git2repo.git2repo(self.repo_url,self.repo_name)
        self.root_dir = code_path
        #print("root:",self.root_dir)
        if platform.system() == 'Darwin' or platform.system() == 'Linux':
            self.repo_path = self.root_dir+ '/commit_guru/ingester/CASRepos/git/' + self.repo_name
            self.file_path = up(self.root_dir) + '/data/commit_guru/' + self.repo_name + '.csv'
            #self.committed_file = up(os.getcwd()) + '/data/committed_files/' + self.repo_name + '_committed_file.pkl'
            self.und_file = up(self.root_dir) + '/data/understand_files/' + self.repo_name + '_understand.csv'
        else:
            self.repo_path = up(os.getcwd()) + '\\temp_repo\\' + self.repo_name
            self.file_path = up(os.getcwd()) + '\\data\\commit_guru\\' + self.repo_name + '.csv'
            self.und_file = up(self.root_dir) + '\\data\\understand_files\\' + self.repo_name + '_understand.csv'
            #self.committed_file = up(os.getcwd()) + '\\data\\committed_files\\' + self.repo_name + '_committed_file.pkl'
        self.buggy_clean_pairs = self.read_commits()
        #self.buggy_clean_pairs = self.buggy_clean_pairs[0:5]
        # Reference current directory, so we can go back after we are done.
        self.cwd = Path('/tmp/smajumd3/')
        #self.repo = self.clone_repo()
        # Generate path to store udb files
        #self.udb_path = self.cwd.joinpath(".temp", "udb")
        self.udb_path = self.cwd.joinpath("temp", "udb/"+self.repo_name)

        # Create a folder to hold the udb files
        if not self.udb_path.is_dir():
            os.makedirs(self.udb_path)

    def read_commits(self):
        print(self.file_path)
        df = pd.read_csv(self.file_path)
        # print(df)
        df = df[df['contains_bug'] == True]
        df = df.reset_index('drop' == True)
        self.commits = []
        commits = []
        temp_2 = df.shape[0]
        print(df.shape)
        for i in range(df.shape[0]):
            try:
                committed_files = []
                if df.loc[i,'parent_hashes'] == None:
                    print("Has a parent")
                    continue
                bug_fixing_commit = df.loc[i,'parent_hashes']
                bug_existing_commit = df.loc[i,'commit_hash']
                files_changed = str(df.loc[i,'fileschanged'])

                #print(files_changed)
                files_changed = files_changed.split(',')
                files_changed = list(filter(('CAS_DELIMITER').__ne__, files_changed))
                self.commits.append(bug_existing_commit)
                #language = "Python"
                language = self.repo_lang
                if bug_fixing_commit == None:
                    print(df.iloc[i,0])
                    continue
                for row in files_changed:
                    if language == "Java" or language == "C++" or language == "C":
                        #if len(row.split('src/')) == 1:
                        #    continue
                        #committed_files.append(row.split('src/')[1].replace('/','.').rsplit('.',1)[0])
                        committed_files.append(row.replace('/', '.').rsplit('.', 1)[0])
                    elif language == "Python" :
                        committed_files.append(row.replace('/', '.').rsplit('.', 1)[0])
                    elif language == "Fortran" :
                        committed_files.append(row['file_path'].replace('/', '.').rsplit('.', 1)[0])
                    else:
                        print("Language under construction")
                commits.append([bug_existing_commit,bug_fixing_commit,committed_files])
            except Exception as e:
                print("exception at reading commits",e)
                continue
        return commits

    def get_defective_pair_metrics(self):
        """
        Use the understand tool's API to generate metrics

        Notes
        -----
        + For every clean and buggy pairs of hashed, do the following:
            1. Get the diff of the files changes
            2. Checkout the snapshot at the buggy commit
            3. Compute the metrics of the files in that commit.
            4. Next, checkout the snapshot at the clean commit.
            5. Compute the metrics of the files in that commit.
        """

        metrics_dataframe = pd.DataFrame()
        for i in range(len(self.buggy_clean_pairs)):
            try:
                buggy_hash = self.buggy_clean_pairs[i][0]
                clean_hash = self.buggy_clean_pairs[i][1]
                files_changed = self.buggy_clean_pairs[i][2]
                if len((files_changed)) == 0:
                     continue
                # Go the the cloned project path

                #------------BUGGY METRICS-----------------
                buggy_und_file = self.udb_path.joinpath("{}_{}.csv".format(self.repo_name+buggy_hash, "buggy"))
                buggy_df = pd.read_csv(buggy_und_file)
                buggy_df.Kind.apply(str)
                #buggy_df = buggy_df[buggy_df['Kind'] == "Class"]
                #buggy_df = buggy_df[buggy_df['Kind'].isin(class_strs)]
                buggy_df = buggy_df[buggy_df['Kind'].str.contains("Class", regex = True)]
                temp_l1 = len(buggy_df)
                if self.repo_lang == "Python":
                    print("modfiy the Name column")
                if self.repo_lang == "Fortran":
                    print("modfiy the Name column")

                #------ Testing area------------
                #new_buggy_df = pd.DataFrame()
                index_list = []
                name_df = buggy_df['Name'].copy()
                for index, name in name_df.iteritems():
                    r = re.compile(str(name))
                    newList = list(filter(r.search, list(set(files_changed))))
                    if len(newList)>0:
                        index_list.append(int(index))
                        #new_buggy_df = new_buggy_df.append(buggy_df.iloc[index])
                        #print("new buggy df is : ", new_buggy_df)
                new_buggy_df = pd.DataFrame()
                if index_list:
                    new_buggy_df = buggy_df.loc[index_list]

                #------- Testing area ends--------

                #new_buggy_df = buggy_df[buggy_df['Name'].isin(list(set(files_changed)))]
                if new_buggy_df.shape[0]!=0:
                    temp = pd.concat([buggy_df, new_buggy_df]).drop_duplicates(keep=False)
                    new_buggy_df["commit_hash"] = buggy_hash
                    new_buggy_df["Bugs"] = 1
                    metrics_dataframe = metrics_dataframe.append(new_buggy_df)
                    temp["commit_hash"] = buggy_hash
                    temp["Bugs"] = 0
                    metrics_dataframe = metrics_dataframe.append(temp)
                else:
                    buggy_df["commit_hash"] = buggy_hash
                    buggy_df["Bugs"] = 0
                    metrics_dataframe = metrics_dataframe.append(buggy_df)

                #------------CLEAN METRICS---------------
                clean_und_file = self.udb_path.joinpath("{}_{}.csv".format(self.repo_name+buggy_hash, "clean"))
                clean_df = pd.read_csv(clean_und_file)
                clean_df = clean_df[clean_df['Kind'].str.contains("Class", regex=True)]
                #clean_df = clean_df[clean_df['Kind'] == "Class"]
                clean_df["commit_hash"] = clean_hash
                clean_df["Bugs"] = 0
                metrics_dataframe = metrics_dataframe.append(clean_df)
                print("commit number "+str(i)+" done")
            except Exception as e:
                print("issue with",buggy_hash)
                print("Error:",e)
                continue
        os.chdir(self.root_dir)
        print(self.root_dir)

        metrics_dataframe.to_csv(self.und_file,index=False)
        print("Created the .csv file")
        return metrics_dataframe
