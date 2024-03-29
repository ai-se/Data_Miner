# -*- coding: utf-8 -*-
"""
Created on Fri Aug 24 15:39:01 2018

@author: suvod
"""
from __future__ import division
import sys
sys.path.append("..")
from pygit2 import clone_repository
from pygit2 import GIT_SORT_TOPOLOGICAL, GIT_SORT_REVERSE,GIT_MERGE_ANALYSIS_UP_TO_DATE,GIT_MERGE_ANALYSIS_FASTFORWARD,GIT_MERGE_ANALYSIS_NORMAL,GIT_RESET_HARD
from pygit2 import Repository
import shutil,os
import pygit2
import re
from utils.utils import utils
from os import listdir
from os.path import isfile, join
from datetime import datetime
import platform
import threading
from multiprocessing import Queue
from threading import Thread
import numpy as np
import itertools
import pandas as pd
from multiprocessing import Pool, cpu_count
from os.path import dirname as up

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

class get_all_branches(object):
    
    def __init__(self,repo_url,repo_name):
        self.repo_url = repo_url
        self.repo_name = repo_name
        self.commit = []
        if platform.system() == 'Darwin' or platform.system() == 'Linux':
            self.repo_path = up(up(os.getcwd())) + '/temp_repo/' + repo_name
        else:
            self.repo_path = up(up(os.getcwd())) + '\\temp_repo\\' + repo_name
        self.clone_repo()
        
        
    def clone_repo(self):
        git_path = pygit2.discover_repository(self.repo_path)
        if git_path is not None:
            self.repo = pygit2.Repository(git_path)
            return self.repo
        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)
        self.repo = clone_repository(self.repo_url, self.repo_path)
        return self.repo
    
    
    def get_branches(self):
        return list(self.repo.branches)

class git2repo(object):
    
    def __init__(self,repo_url,repo_name):
        self.repo_url = repo_url
        self.repo_name = repo_name
        self.repos = []
        if platform.system() == 'Darwin' or platform.system() == 'Linux':
            self.repo_path = os.getcwd() + '/temp_repo/' + repo_name
        else:
            self.repo_path = os.getcwd() + '\\temp_repo\\' + repo_name
        self.cores = cpu_count()
        
    def clone_repo(self):
        git_path = pygit2.discover_repository(self.repo_path)
        if git_path is not None:
            self.repo = pygit2.Repository(git_path)
            return self.repo
        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)
        self.repo = clone_repository(self.repo_url, self.repo_path)
        return self.repo

    def clone_branch(self,branch):
        repo_path = self.repo_path + '_' + branch
        git_path = pygit2.discover_repository(repo_path)
        if git_path is not None:
            self.repo = pygit2.Repository(git_path)
            return self.repo
        if not os.path.exists(repo_path):
            os.makedirs(repo_path)
        self.repo = clone_repository(self.repo_url, repo_path,checkout_branch = branch)
        return self.repo

    def clone_master_branch(self):
        repo_path = self.repo_path
        git_path = pygit2.discover_repository(repo_path)
        if git_path is not None:
            self.repo = pygit2.Repository(git_path)
            return self.repo
        if not os.path.exists(repo_path):
            os.makedirs(repo_path)
        self.repo = clone_repository(self.repo_url, repo_path,checkout_branch = 'master')
        return self.repo
    
    def get_branches(self):
        gb = get_all_branches(self.repo_url,self.repo_name)
        gb.clone_repo()
        return gb.get_branches()[1:]
    
    def repo_remove(self):
        self.repo.free()
        if platform.system() == 'Darwin' or platform.system() == 'Linux':
            deldir = self.repo_path + '/.git/objects/pack'
        else:
            deldir = self.repo_path + '\\.git\\objects\\pack'
        delFiles = [f for f in listdir(deldir) if isfile(join(deldir, f))]
        print(delFiles)
        if len(delFiles) > 0:   
            for i in delFiles:
                if platform.system() == 'Darwin' or platform.system() == 'Linux':
                    file_name = deldir + '/' + i
                else:
                    file_name = deldir + '\\' + i
                os.chmod(file_name, 0o777)
            if os.path.exists(self.repo_path):
                shutil.rmtree(self.repo_path,ignore_errors=True)
            
    def branch_remove(self,repo,path):
        repo.free()
        if platform.system() == 'Darwin' or platform.system() == 'Linux':
            deldir = path + '/.git/objects/pack'
        else:
            deldir = path + '\\.git\\objects\\pack'
        delFiles = [f for f in listdir(deldir) if isfile(join(deldir, f))]
        for i in delFiles:
            if platform.system() == 'Darwin' or platform.system() == 'Linux':
                file_name = deldir + '/' + i
            else:
                file_name = deldir + '\\' + i
            os.chmod(file_name, 0o777)
        if os.path.exists(path):
            shutil.rmtree(path,ignore_errors=True)
     
        
    def get_current_commit_objects(self):
        commits = []
        commit_objs = []
        for commit in self.repo.walk(self.repo.head.target, GIT_SORT_TOPOLOGICAL | GIT_SORT_REVERSE):
            commit_id = commit.id.hex
            commit_message = commit.message
            res=re.search(r'\b{bug|fix|issue|error|patch|defect|problem|wrong|fail|resol|#}\b',utils().stemming(commit_message),re.IGNORECASE)
            if res is not None:
                commits_buggy = 1
            else:
                commits_buggy = 0
            if len(commit.parent_ids) == 0:
                commit_parent = None
            else:
                commit_parent = commit.parent_ids[0].hex
            commit_objs.append(commit)
            commits.append([commit_id,commit_message,commit_parent,commits_buggy,self.repo.head.name,commit.commit_time])
        self.commit = commit_objs
        return commits
    
    def get_commit_data(self,branch):
        commits = []
        commit_objs = []
        repo = self.clone_branch(branch)
        #print(branch, "++++++")
        path = self.repo_path + '_' + branch
        for commit in repo.walk(repo.head.target, GIT_SORT_TOPOLOGICAL | GIT_SORT_REVERSE):
            commit_id = commit.id.hex
            commit_message = commit.message
            res=re.search(r'\b{bug|fix|issue|error|patch|defect|problem|wrong|fail|resol|#}\b',utils().stemming(commit_message),re.IGNORECASE)
            if res is not None:
                commits_buggy = 1
            else:
                commits_buggy = 0
            if len(commit.parent_ids) == 0:
                commit_parent = None
            else:
                commit_parent = commit.parent_ids[0].hex
            commit_objs.append(commit)
            commits.append([commit_id,commit_message,commit_parent,commits_buggy,branch,commit.commit_time])
        #print(commit_objs)
        self.repos.append([repo,path]) 
        return commits,commit_objs

        

    def get_commit_objects(self):
        commits = []
        threads = []
        commits = []
        commit_objs = []
        branches = self.get_branches()
        #print("at git commit objects")
        self.repo_remove()
        for branch in branches:
            branch= branch.split("/",1)[1]
            t = ThreadWithReturnValue(target = self.get_commit_data, args = [branch])
            threads.append(t)
        for i in range(0,len(threads),self.cores):
            _threads = threads[i:i+self.cores]
            for th in _threads:
                th.start()
            for th in _threads:
                response1,response2 = th.join()
                commits.append(response1)
                commit_objs.append(response2)
        self.clone_repo()
        commits = list(itertools.chain.from_iterable(commits))
        commit_objs = list(itertools.chain.from_iterable(commit_objs))
        self.commit = commit_objs
        return commits
    
    
    def get_committed_files(self): #changes for making commited files work
        committed_files = []
        commits = self.commit
        explored_commits = []
        for i in range(len(commits)):
            try:
                explored_commits.append(commits[i].id.hex)
                if len(commits[i].parents) == 0:  # need to handle this case where commit doesnot have a parent
                    continue
                t0 = commits[i]
                if i != 0:
                    t1 = commits[i].parents[0]
                else:
                    continue
                _diff = self.repo.diff(t1,t0)
                for j in _diff.deltas:
                    committed_files.append([commits[i].id.hex,j.new_file.id.hex, j.new_file.mode,j.new_file.path])
            except:
                print("commit:",commits[i].id)
                continue
        for j in range(len(self.repos)):
            self.branch_remove(self.repos[j][0],self.repos[j][1])
        return committed_files
    
    def get_diffs(self,commits):
        diffs = {}
        for i in range(len(commits)):
            t0 = self.repo.get(commits[i])
            files = {}
            if len(t0.parents) == 0:  # need to handle this case where commit doesnot have a parent
                continue
            if i != 0:
                t1 = t0.parents[0]
            else:
                continue
            _diff = self.repo.diff(t1,t0)
            for diff_i in _diff.__iter__():
                file_path = diff_i.delta.new_file.path
                old_lineno = []
                new_lineno = []
                for x in diff_i.hunks:
                    for y in x.lines:
                        old_lineno.append(y.old_lineno)
                        new_lineno.append(y.new_lineno)
                files[diff_i.delta.new_file.id] = {'file_path':file_path, 'old_lines':old_lineno,'new_lines':new_lineno}
            diffs[t0.id] = {'files':files,'object':t0}
        return diffs
    
    def get_blame(self,file_path):
        return self.repo.blame(file_path,flags = 'GIT-BLAME_TRACK_COPIES_ANY_COMMIT_COPIES')
    
    
    def get_commits(self,all=True):
        if all:
            _commits = self.get_commit_objects()
        else:
            _commits = self.get_current_commit_objects()
        return _commits
        
