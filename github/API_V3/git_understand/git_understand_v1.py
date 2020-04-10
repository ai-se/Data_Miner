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

# class ThreadWithReturnValue(Thread):
#     def __init__(self, group=None, target=None, name=None,
#                  args=(), kwargs={}, Verbose=None):
#         Thread.__init__(self, group, target, name, args, kwargs)
#         self._return = None
#     def run(self):
#         #print(type(self._target))
#         if self._target is not None:
#             self._return = self._target(*self._args,
#                                                 **self._kwargs)
#     def join(self, *args):
#         Thread.join(self, *args)
#         return self._return


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
        # Reference current directory, so we can go back after we are done.
        self.cwd = Path('/home/suvodeep/Documents/AI4SE/Data_Miner/github/API_V3/suvodeep/')
        self.cores = cpu_count()
        #self.repo = self.clone_repo()
        # if self.repo == None:
        #     raise ValueError
        # else:
        #     print(self.repo)

        # Generate path to store udb files
        print("cwd",self.cwd)
        self.udb_path = self.cwd.joinpath("temp", "udb/"+self.repo_name)
        print("udb at init",self.udb_path)

        # Create a folder to hold the udb files
        if not self.udb_path.is_dir():
            os.makedirs(self.udb_path)

        # Generate source path where the source file exist
        #self.source_path = self.cwd.joinpath(
        #    ".temp", "sources", self.repo_name)

    def clone_repo(self):
        git_path = pygit2.discover_repository(self.repo_path)
        if git_path is not None:
            self.repo = pygit2.Repository(git_path)
            return self.repo
        self.repo = None
        return self.repo

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
                #files_changed = df.loc[i,'fileschanged']
                #print(files_changed)
                #files_changed = files_changed.split(',')
                #files_changed = list(filter(('CAS_DELIMITER').__ne__, files_changed))
                self.commits.append(bug_existing_commit)
                if bug_fixing_commit == None:
                    print(df.iloc[i,0])
                    continue
                #for row in files_changed:
                #    if len(row.split('src/')) == 1:
                #        continue
                #    committed_files.append(row.split('src/')[1].replace('/','.').rsplit('.',1)[0])
                commits.append([bug_existing_commit,bug_fixing_commit])
            except:
              continue
        return commits

    #@staticmethod
    def _os_cmd(self,cmd, verbose=False):
        """
        Run a command on the shell

        Parameters
        ----------
        cmd: str
            A command to run.
        """
        cmd = shlex.split(cmd)
        with sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.DEVNULL) as p:
            out, err = p.communicate()
        if verbose:
            print(out)
            print(err)
        return out, err

    def generate_repo_path(self):
        def randomStringDigits(stringLength=6):
            """Generate a random string of letters and digits """
            lettersAndDigits = string.ascii_letters + string.digits
            return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))
        ukey = randomStringDigits(8)  
        return ukey
    
    
    # def _create_und_files(self, file_name_suffix):
    #     """
    #     Creates understand project files
    #     Parameters
    #     ----------
    #     file_name_suffix : str
    #         A suffix for the understand_filenames
    #     """
    #     # Create a handle for storing *.udb file for the project
    #     und_file = self.udb_path.joinpath(
    #         "{}_{}.udb".format(self.repo_name, file_name_suffix))
    #     # Go to the udb path
    #     os.chdir(self.udb_path)
    #     # find and replace all F90 to f90
    #     for filename in glob(os.path.join(self.repo_path, '*/**')):
    #         if ".F90" in filename:
    #             os.rename(filename, filename[:-4] + '.f90')

    #     # Generate udb file
    #     if self.repo_lang == "fortran":
    #         cmd = "und create -languages Fortran add {} analyze {}".format(
    #             str(self.repo_path), str(und_file))
    #     elif self.repo_lang == "python":
    #         cmd = "und create -languages python add {} analyze {}".format(
    #             str(self.repo_path), str(und_file))
    #     elif self.repo_lang == "C":
    #         cmd = "und create -languages C++ add {} analyze {}".format(
    #             str(self.repo_path), str(und_file))
    #     elif self.repo_lang == "C++":
    #         cmd = "und create -languages C++ add {} analyze {}".format(
    #             str(self.repo_path), str(und_file))
    #     elif self.repo_lang == "Java":
    #         cmd = "und create -languages Java add {} analyze {}".format(
    #             str(self.repo_path), str(und_file))
    #     elif self.repo_lang == "C#":
    #         cmd = "und create -languages C# add {} analyze {}".format(
    #             str(self.repo_path), str(und_file))
    #     elif self.repo_lang == "JavaScript":
    #         cmd = "und create -languages JavaScript add {} analyze {}".format(
    #             str(self.repo_path), str(und_file))
    #     out, err = self._os_cmd(cmd)

    #     if file_name_suffix == "buggy":
    #         self.buggy_und_file = und_file
    #     elif file_name_suffix == "clean":
    #         self.clean_und_file = und_file

    def _create_und_files_v1(self, file_name_suffix,buggy_hash):
        """
        Creates understand project files
        Parameters
        ----------
        file_name_suffix : str
            A suffix for the understand_filenames
        """
        # Create a handle for storing *.udb file for the project
        und_file = self.udb_path.joinpath(
            "{}_{}.udb".format(self.repo_name+buggy_hash, file_name_suffix))
        und_file_csv = self.udb_path.joinpath(
            "{}_{}.csv".format(self.repo_name+buggy_hash, file_name_suffix))
        # Go to the udb path
        print("at und file",self.repo_name,self.udb_path,und_file)
        os.chdir(self.udb_path)
        # find and replace all F90 to f90
        for filename in glob(os.path.join(self.repo_path, '*/**')):
            if ".F90" in filename:
                os.rename(filename, filename[:-4] + '.f90')

        # Generate udb file
        if self.repo_lang == "fortran":
            cmd = "und create -languages Fortran add {} settings -metrics all -metricsOutputFile {} analyze {} metrics".format(
                str(self.repo_path),str(und_file_csv) ,str(und_file))
        elif self.repo_lang == "Python":
            cmd = "und create -languages python add {} settings -metrics all -metricsOutputFile {} analyze {} metrics".format(
                str(self.repo_path),str(und_file_csv) ,str(und_file))
        elif self.repo_lang == "C":
            cmd = "und create -languages C++ add {} settings -metrics all -metricsOutputFile {} analyze {} metrics".format(
                str(self.repo_path),str(und_file_csv) ,str(und_file))
        elif self.repo_lang == "C++":
            cmd = "und create -languages C++ add {} settings -metrics all -metricsOutputFile {} analyze {} metrics".format(
                str(self.repo_path),str(und_file_csv) ,str(und_file))
        elif self.repo_lang == "Java":
            cmd = "und create -languages Java add {} settings -metrics all -metricsOutputFile {} analyze {} metrics".format(
                str(self.repo_path),str(und_file_csv) ,str(und_file))
        elif self.repo_lang == "C#":
            cmd = "und create -languages C# add {} settings -metrics all -metricsOutputFile {} analyze {} metrics".format(
                str(self.repo_path),str(und_file_csv) ,str(und_file))
        elif self.repo_lang == "JavaScript":
            cmd = "und create -languages JavaScript add {} -metrics all -metricsOutputFile {} analyze {} metrics".format(
                str(self.repo_path),str(und_file_csv) ,str(und_file))
        out, err = self._os_cmd(cmd)
        #print("runnung command")
        out, err = self._os_cmd(cmd)
        #print("command done")

        if file_name_suffix == "buggy":
            self.buggy_und_file = und_file
        elif file_name_suffix == "clean":
            self.clean_und_file = und_file

        # Go to the cloned repo
        os.chdir(self.repo_path)
        
    
    # def _files_changed_in_git_diff(self, hash_1, hash_2):
    #     """
    #     Get a list of all the files changed between two hashes

    #     Parameters
    #     ----------
    #     hash_1 : str
    #         Commit hash 1.
    #     hash_2 : bool
    #         Commit hash 2.

    #     Returns
    #     -------
    #     List[str]:
    #         A list of all files changed. For simplicity we only include *.py
    #         *.F90, *.c, *.cpp, *.java.
    #     """

    #     os.chdir(self.repo_path)
    #     out, __ = self._os_cmd(
    #         "git diff {} {} --name-only".format(hash_1.id.hex, hash_2.id.hex))
    #     files_changed = []
    #     for file in out.splitlines():
    #         for wanted in [".py", ".c", ".cpp", ".F90", ".f90", ".java"]:
    #             if wanted in str(file) and "__init__.py" not in str(file):
    #                 files_changed.append(Path(str(file)).name[:-1])

    #     # A work around for FORTRAN file extensions.
    #     if self.repo_lang == "fortran":
    #         files_changed = list(map(lambda x: x[:-4]+".f90", files_changed))

    #     return files_changed
    

    # def get_defective_pair_metrics(self):
    #     """
    #     Use the understand tool's API to generate metrics

    #     Notes
    #     -----
    #     + For every clean and buggy pairs of hashed, do the following:
    #         1. Get the diff of the files changes
    #         2. Checkout the snapshot at the buggy commit
    #         3. Compute the metrics of the files in that commit.
    #         4. Next, checkout the snapshot at the clean commit.
    #         5. Compute the metrics of the files in that commit.
    #     """

    #     metrics_dataframe = pd.DataFrame()
    #     print(len(self.buggy_clean_pairs))
    #     for i in range(len(self.buggy_clean_pairs)):
    #         try:
    #             buggy_hash = self.buggy_clean_pairs[i][0]
    #             clean_hash = self.buggy_clean_pairs[i][1]
    #             files_changed = self.buggy_clean_pairs[i][2]
    #             if len((files_changed)) == 0:
    #                 continue
    #             print(i,(buggy_hash, clean_hash))
    #             # Go the the cloned project path
    #             os.chdir(self.repo_path)
    #             # Checkout the master branch first, we'll need this
    #             # to find what files have changed.
    #             self._os_cmd("git reset --hard master", verbose=False)
    #             #print("reset done")

    #             # Get a list of files changed between the two hashes
    #             #files_changed = self._files_changed_in_git_diff(
    #             #    buggy_hash, clean_hash)
    #             # ------------------------------------------------------------------
    #             # ---------------------- BUGGY FILES METRICS -----------------------
    #             # ------------------------------------------------------------------
    #             # Checkout the buggy commit hash
    #             self._os_cmd(
    #                 "git reset --hard {}".format(buggy_hash), verbose=False)
    #             #print("checkout done")

    #             # Create a understand file for this hash
    #             self._create_und_files("buggy")

    #             #print(self.buggy_und_file)
    #             db_buggy = und.open(str(self.buggy_und_file))
    #             #print("file opened")
    #             #print("Files",set(files_changed))
    #             for file in db_buggy.ents("Class"):
    #                 # print directory name
    #                 #print(file,file.longname(), file.kind())
    #                 r = re.compile(str(file.longname()))
    #                 # print(file.longname())
    #                 newlist = list(filter(r.search, list(set(files_changed))))
    #                 #print(newlist)
    #                 if len(newlist) > 0:
    #                     metrics = file.metric(file.metrics())
    #                     metrics["commit_hash"] = buggy_hash
    #                     metrics["Name"] = file.longname()
    #                     metrics["Bugs"] = 1
    #                     metrics_dataframe = metrics_dataframe.append(
    #                         pd.Series(metrics), ignore_index=True)
    #                 else:
    #                     metrics = file.metric(file.metrics())
    #                     metrics["commit_hash"] = buggy_hash
    #                     metrics["Name"] = file.longname()
    #                     metrics["Bugs"] = 0
    #                     metrics_dataframe = metrics_dataframe.append(
    #                         pd.Series(metrics), ignore_index=True)
    #             # Purge und file
    #             db_buggy.close()
    #             #break
    #             self._os_cmd("rm {}".format(str(self.buggy_und_file)))
    #             # ------------------------------------------------------------------
    #             # ---------------------- CLEAN FILES METRICS -----------------------
    #             # ------------------------------------------------------------------
    #             # Checkout the clean commit hash
    #             self._os_cmd(
    #                 "git reset --hard {}".format(clean_hash), verbose=False)

    #             # Create a understand file for this hash
    #             self._create_und_files("clean")
    #             db_clean = und.open(str(self.clean_und_file))
    #             for file in db_clean.ents("class"):
    #                 # print directory name
    #                 r = re.compile(str(file.longname()))
    #                 newlist = list(filter(r.search, files_changed))
    #                 #if str(file) in files_changed:
    #                 if len(newlist) > 0:
    #                     metrics = file.metric(file.metrics())
    #                     #print(metrics)
    #                     metrics["commit_hash"] = clean_hash
    #                     metrics["Name"] = file.name()
    #                     metrics["Bugs"] = 0
    #                     metrics_dataframe = metrics_dataframe.append(
    #                         pd.Series(metrics), ignore_index=True)
    #                 else:
    #                     metrics = file.metric(file.metrics())
    #                     #print(metrics)
    #                     metrics["commit_hash"] = clean_hash
    #                     metrics["Name"] = file.name()
    #                     metrics["Bugs"] = 0
    #                     metrics_dataframe = metrics_dataframe.append(
    #                         pd.Series(metrics), ignore_index=True)
    #             db_clean.close()
    #             # Purge und file
    #             self._os_cmd("rm {}".format(str(self.clean_und_file)))
    #         except Exception as e:
    #             print("issue with",buggy_hash)
    #             print("Error:",e)
    #             continue
    #         # print(self.metrics_dataframe)

    #         #printProgressBar(i, len(self.buggy_clean_pairs),
    #         #                 prefix='Progress:', suffix='Complete', length=50)
    #     os.chdir(self.root_dir)
    #     metrics_dataframe.to_csv(self.und_file,index=False)
    #     return metrics_dataframe


    def get_defective_pair_udb_files(self):
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
                #files_changed = self.buggy_clean_pairs[i][2]
                # if len((files_changed)) == 0:
                #     continue
                print(i,self.repo_name,(buggy_hash, clean_hash))
                # Go the the cloned project path
                os.chdir(self.repo_path)
                # Checkout the master branch first, we'll need this
                # to find what files have changed.
                self._os_cmd("git reset --hard master", verbose=False)

                # Get a list of files changed between the two hashes
                #files_changed = self._files_changed_in_git_diff(
                #    buggy_hash, clean_hash)
                # ------------------------------------------------------------------
                # ---------------------- BUGGY FILES METRICS -----------------------
                # ------------------------------------------------------------------
                # Checkout the buggy commit hash
                self._os_cmd(
                    "git reset --hard {}".format(buggy_hash), verbose=False)

                # Create a understand file for this hash
                self._create_und_files_v1("buggy",buggy_hash)

                self._os_cmd(
                    "git reset --hard {}".format(clean_hash), verbose=False)

                self._create_und_files_v1("clean",buggy_hash)
            except ValueError as e:
                print("issue with",buggy_hash)
                print("Error:",e)
                continue
            # print(self.metrics_dataframe)

            #printProgressBar(i, len(self.buggy_clean_pairs),
            #                 prefix='Progress:', suffix='Complete', length=50)
        os.chdir(self.root_dir)
        #metrics_dataframe.to_csv(self.und_file,index=False)
        return metrics_dataframe
