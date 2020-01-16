#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  5 18:54:29 2019

@author: suvodeepmajumder
"""
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

    ddef __init__(self,repo_url,repo_name,repo_lang,code_path):
        self.repo_url = repo_url
        self.repo_name = repo_name
        self.repo_lang = repo_lang
        #self.repo_obj = git2repo.git2repo(self.repo_url,self.repo_name)
        self.root_dir = code_path
        print("root:",self.root_dir)
        if platform.system() == 'Darwin' or platform.system() == 'Linux':
            self.repo_path = self.root_dir+ '/commit_guru/ingester/CASRepos/git/' + self.repo_name
            self.file_path = up(self.root_dir) + '/data/commit_guru/' + self.repo_name + '.csv'
            #self.committed_file = up(os.getcwd()) + '/data/committed_files/' + self.repo_name + '_committed_file.pkl'
            self.und_file = up(self.root_dir) + '/data/understand_files/' + self.repo_name + '_understand.csv'
        else:
            self.repo_path = up(os.getcwd()) + '\\temp_repo\\' + self.repo_name
            self.file_path = up(os.getcwd()) + '\\data\\commit_guru\\' + self.repo_name + '.pkl'
            #self.committed_file = up(os.getcwd()) + '\\data\\committed_files\\' + self.repo_name + '_committed_file.pkl'
        self.buggy_clean_pairs = self.read_commits()
        #self.buggy_clean_pairs = self.buggy_clean_pairs[0:5]
        # Reference current directory, so we can go back after we are done.
        self.cwd = Path(self.root_dir)
        #self.repo = self.clone_repo()
        # Generate path to store udb files
        self.udb_path = self.cwd.joinpath(".temp", "udb")

        # Create a folder to hold the udb files
        if not self.udb_path.is_dir():
            os.makedirs(self.udb_path)

    def read_commits(self):
        df = pd.read_csv(self.file_path)
        # print(df)
        df = df[df['contains_bug'] == True]
        df = df.reset_index('drop' == True)
        self.commits = []
        commits = []
        for i in range(df.shape[0]):
            try:
                committed_files = []
                if df.loc[i,'parent_hashes'] == None:
                    continue
                bug_fixing_commit = df.loc[i,'parent_hashes']
                bug_existing_commit = df.loc[i,'commit_hash']
                files_changed = df.loc[i,'fileschanged']
                #print(files_changed)
                files_changed = files_changed.split(',')
                files_changed = list(filter(('CAS_DELIMITER').__ne__, files_changed))
                self.commits.append(bug_existing_commit)
                if bug_fixing_commit == None:
                    print(df.iloc[i,0])
                    continue
                for row in files_changed:
                    if len(row.split('src/')) == 1:
                        continue
                    committed_files.append(row.split('src/')[1].replace('/','.').rsplit('.',1)[0])
                commits.append([bug_existing_commit,bug_fixing_commit,committed_files])
            except:
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
        print(len(self.buggy_clean_pairs))
        for i in range(len(self.buggy_clean_pairs)):
            try:
                buggy_hash = self.buggy_clean_pairs[i][0]
                clean_hash = self.buggy_clean_pairs[i][1]
                files_changed = self.buggy_clean_pairs[i][2]
                if len((files_changed)) == 0:
                    continue
                print(i,(buggy_hash, clean_hash))
                # Go the the cloned project path
                buggy_und_file = self.udb_path.joinpath("{}_{}.udb".format(self.repo_name+buggy_hash, "buggy"))
                #print(self.buggy_und_file)
                db_buggy = und.open(str(buggy_und_file))
                #print("Files",set(files_changed))
                for file in db_buggy.ents("Class"):
                    # print directory name
                    #print(file,file.longname(), file.kind())
                    r = re.compile(str(file.longname()))
                    # print(file.longname())
                    newlist = list(filter(r.search, list(set(files_changed))))
                    #print(newlist)
                    if len(newlist) > 0:
                        metrics = file.metric(file.metrics())
                        metrics["commit_hash"] = buggy_hash
                        metrics["Name"] = file.longname()
                        metrics["Bugs"] = 1
                        metrics_dataframe = metrics_dataframe.append(
                            pd.Series(metrics), ignore_index=True)
                    else:
                        metrics = file.metric(file.metrics())
                        metrics["commit_hash"] = buggy_hash
                        metrics["Name"] = file.longname()
                        metrics["Bugs"] = 0
                        metrics_dataframe = metrics_dataframe.append(
                            pd.Series(metrics), ignore_index=True)
                # Purge und file
                db_buggy.close()
                clean_und_file = self.udb_path.joinpath("{}_{}.udb".format(self.repo_name+buggy_hash, "buggy"))
                db_clean = und.open(str(clean_und_file))
                for file in db_clean.ents("class"):
                    # print directory name
                    r = re.compile(str(file.longname()))
                    newlist = list(filter(r.search, files_changed))
                    #if str(file) in files_changed:
                    if len(newlist) > 0:
                        metrics = file.metric(file.metrics())
                        #print(metrics)
                        metrics["commit_hash"] = clean_hash
                        metrics["Name"] = file.name()
                        metrics["Bugs"] = 0
                        metrics_dataframe = metrics_dataframe.append(
                            pd.Series(metrics), ignore_index=True)
                    else:
                        metrics = file.metric(file.metrics())
                        #print(metrics)
                        metrics["commit_hash"] = clean_hash
                        metrics["Name"] = file.name()
                        metrics["Bugs"] = 0
                        metrics_dataframe = metrics_dataframe.append(
                            pd.Series(metrics), ignore_index=True)
                db_clean.close()
                # Purge und file
            except Exception as e:
                print("issue with",buggy_hash)
                print("Error:",e)
                continue
        os.chdir(self.root_dir)
        metrics_dataframe.to_csv(self.und_file,index=False)
        return metrics_dataframe