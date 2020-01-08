#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  5 18:54:29 2019

@author: suvodeepmajumder
"""
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
import os
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

    def __init__(self,repo_url,repo_name,repo_lang):
        self.repo_url = repo_url
        self.repo_name = repo_name
        self.repo_lang = repo_lang
        self.repo_obj = git2repo.git2repo(self.repo_url,self.repo_name)
        self.repo = self.repo_obj.clone_repo()
        self.root_dir = os.getcwd()
        if platform.system() == 'Darwin' or platform.system() == 'Linux':
            self.repo_path = up(os.getcwd()) + '/temp_repo/' + self.repo_name
            self.file_path = up(os.getcwd()) + '/data/commit/' + self.repo_name + '_commit.pkl'
            self.committed_file = up(os.getcwd()) + '/data/committed_files/' + self.repo_name + '_committed_file.pkl'
        else:
            self.repo_path = up(os.getcwd()) + '\\temp_repo\\' + self.repo_name
            self.file_path = up(os.getcwd()) + '\\data\\commit\\' + self.repo_name + '_commit.pkl'
            self.committed_file = up(os.getcwd()) + '\\data\\committed_files\\' + self.repo_name + '_committed_file.pkl'
        self.buggy_clean_pairs = self.read_commits()
        #self.repo_path = self.repo_obj.repo_path
        # Reference current directory, so we can go back after we are done.
        self.cwd = Path(os.getcwd())
        self.cores = cpu_count()

        # Generate path to store udb files
        self.udb_path = self.cwd.joinpath(".temp", "udb")

        # Create a folder to hold the udb files
        if not self.udb_path.is_dir():
            os.makedirs(self.udb_path)

        # Generate source path where the source file exist
        self.source_path = self.cwd.joinpath(
            ".temp", "sources", self.repo_name)

    def clone_repo(self,repo_path):
        git_path = pygit2.discover_repository(repo_path)
        if git_path is not None:
            repo = pygit2.Repository(git_path)
            return repo
        if not os.path.exists(repo_path):
            os.makedirs(repo_path)
        repo = clone_repository(self.repo_url, repo_path)
        return repo

    def generate_repo_path(self):
        def randomStringDigits(stringLength=6):
            """Generate a random string of letters and digits """
            lettersAndDigits = string.ascii_letters + string.digits
            return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))
        ukey = randomStringDigits(8)    
        if platform.system() == 'Darwin' or platform.system() == 'Linux':
            repo_path = up(os.getcwd()) + '/temp_repo/' + ukey + '/' + self.repo_name
        else:
            repo_path = up(os.getcwd()) + '\\temp_repo\\' + ukey + '\\' + self.repo_name
        return repo_path


    def read_commits(self):
        df = pd.read_pickle(self.file_path)
        df_committed_file = pd.read_pickle(self.committed_file)
        df = df[df['buggy'] == True]
        df_commits = df.drop(labels = ['message','buggy'], axis = 1)
        self.commits = []
        commits = []
        for i in range(df_commits.shape[0]):
            committed_files = []
            if df_commits.iloc[i,0] == None or df_commits.iloc[i,1] == None:
                continue
            bug_fixing_commit = self.repo.get(df_commits.iloc[i,0])
            bug_existing_commit = self.repo.get(df_commits.iloc[i,1])
            self.commits.append(bug_fixing_commit)
            if bug_fixing_commit == None:
                print(df_commits.iloc[i,0])
                continue
            for index,row in  df_committed_file[df_committed_file['commit_id'] == df_commits.iloc[i,0]].iterrows():
                if len(row['file_path'].split('src/')) == 1:
                    continue
                committed_files.append(row['file_path'].split('src/')[1].replace('/','.').rsplit('.',1)[0])
            commits.append([bug_existing_commit,bug_fixing_commit,committed_files])
        return commits

    @staticmethod
    def _os_cmd(cmd, verbose=False):
        """
        Run a command on the shell

        Parameters
        ----------
        cmd: str
            A command to run.
        """
        cmd = shlex.split(cmd)
        #print(cmd)
        with sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.DEVNULL) as p:
            out, err = p.communicate()

        if verbose:
            print(out)
            print(err)
        return out, err
    
    
    def _create_und_files(self, file_name_suffix,repo_path,_hash):
        """
        Creates understand project files
        Parameters
        ----------
        file_name_suffix : str
            A suffix for the understand_filenames
        """
        # Create a handle for storing *.udb file for the project
        und_file = self.udb_path.joinpath(
            "{}_{}_{}.udb".format(self.repo_name, _hash ,file_name_suffix))
        # Go to the udb path
        print(und_file)
        os.chdir(self.udb_path)

        # find and replace all F90 to f90
        for filename in glob(os.path.join(repo_path, '*/**')):
            if ".F90" in filename:
                os.rename(filename, filename[:-4] + '.f90')

        # Generate udb file
        if self.repo_lang == "fortran":
            cmd = "/Applications/Understand.app/Contents/MacOS/und create -languages Fortran add {} analyze {}".format(
                str(repo_path), str(und_file))
        elif self.repo_lang == "python":
            cmd = "/Applications/Understand.app/Contents/MacOS/und create -languages python add {} analyze {}".format(
                str(repo_path), str(und_file))
        elif self.repo_lang == "C":
            cmd = "/Applications/Understand.app/Contents/MacOS/und create -languages C++ add {} analyze {}".format(
                str(repo_path), str(und_file))
        elif self.repo_lang == "java":
            cmd = "/Applications/Understand.app/Contents/MacOS/und create -languages Java add {} analyze {}".format(
                str(repo_path), str(und_file))
        out, err = self._os_cmd(cmd)
        print(out, err)

        if file_name_suffix == "buggy":
            self.buggy_und_file = und_file
        elif file_name_suffix == "clean":
            self.clean_und_file = und_file

        # Go to the cloned repo
        os.chdir(repo_path)
        return und_file
        
    
    def get_defective_pair_metrics(self,commit_pairs):
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
        repo_path = self.generate_repo_path()
        repo = self.clone_repo(repo_path)
        metrics_dataframe = pd.DataFrame()
        # print(len(commit_pairs))
        for i in range(len(commit_pairs)):
            buggy_hash = commit_pairs[i][0]
            clean_hash = commit_pairs[i][1]
            files_changed = commit_pairs[i][2]
            if len((files_changed)) == 0:
                continue
            print(i,(buggy_hash.id.hex, clean_hash.id.hex))
            # Go the the cloned project path
            os.chdir(repo_path)
            # Checkout the master branch first, we'll need this
            # to find what files have changed.
            print(os.getcwd(),"resetting repo")
            self._os_cmd("git reset --hard master", verbose=False)
            print(os.getcwd(),"resetting repo Done")
            # Get a list of files changed between the two hashes
            #files_changed = self._files_changed_in_git_diff(
            #    buggy_hash, clean_hash)
            # ------------------------------------------------------------------
            # ---------------------- BUGGY FILES METRICS -----------------------
            # ------------------------------------------------------------------
            # Checkout the buggy commit hash
            self._os_cmd(
                "git reset --hard {}".format(buggy_hash.id.hex), verbose=False)
            print("resetting git done")
            # Create a understand file for this hash
            buggy_und_file = self._create_und_files("buggy",repo_path,buggy_hash.id.hex)
            print("running understand done")
            #print(self.buggy_und_file)
            db_buggy = und.open(str(buggy_und_file))
            #print("Files",set(files_changed))
            for file in db_buggy.ents("Class"):
                # print directory name
                #print(file,file.longname(), file.kind())
                r = re.compile(str(file.longname()))
                print(file.longname())
                newlist = list(filter(r.search, list(set(files_changed))))
                #print(newlist)
                if len(newlist) > 0:
                    metrics = file.metric(file.metrics())
                    metrics["commit_hash"] = buggy_hash.id.hex
                    metrics["Name"] = file.longname()
                    metrics["Bugs"] = 1
                    metrics_dataframe = metrics_dataframe.append(
                        pd.Series(metrics), ignore_index=True)
                else:
                    metrics = file.metric(file.metrics())
                    metrics["commit_hash"] = buggy_hash.id.hex
                    metrics["Name"] = file.longname()
                    metrics["Bugs"] = 0
                    metrics_dataframe = metrics_dataframe.append(
                        pd.Series(metrics), ignore_index=True)
            # Purge und file
            db_buggy.close()
            #break
            self._os_cmd("rm {}".format(str(buggy_und_file)))
            # ------------------------------------------------------------------
            # ---------------------- CLEAN FILES METRICS -----------------------
            # ------------------------------------------------------------------
            # Checkout the clean commit hash
            self._os_cmd(
                "git reset --hard {}".format(clean_hash.id.hex), verbose=False)

            # Create a understand file for this hash
            clean_und_file = self._create_und_files("clean",repo_path,clean_hash.id.hex)
            db_clean = und.open(str(clean_und_file))
            for file in db_clean.ents("class"):
                # print directory name
                r = re.compile(str(file.longname()))
                newlist = list(filter(r.search, files_changed))
                #if str(file) in files_changed:
                if len(newlist) > 0:
                    metrics = file.metric(file.metrics())
                    #print(metrics)
                    metrics["commit_hash"] = clean_hash.id.hex
                    metrics["Name"] = file.name()
                    metrics["Bugs"] = 0
                    metrics_dataframe = metrics_dataframe.append(
                        pd.Series(metrics), ignore_index=True)
                else:
                    metrics = file.metric(file.metrics())
                    #print(metrics)
                    metrics["commit_hash"] = clean_hash.id.hex
                    metrics["Name"] = file.name()
                    metrics["Bugs"] = 0
                    metrics_dataframe = metrics_dataframe.append(
                        pd.Series(metrics), ignore_index=True)
            db_clean.close()
            # Purge und file
            self._os_cmd("rm {}".format(str(clean_und_file)))
            # print(self.metrics_dataframe)

            #printProgressBar(i, len(self.buggy_clean_pairs),
            #                 prefix='Progress:', suffix='Complete', length=50)
        os.chdir(self.root_dir)
        return metrics_dataframe

    def run(self):
        threads = []
        self.buggy_clean_pairs = self.buggy_clean_pairs[0:20]
        print(len(self.buggy_clean_pairs))
        # column_names = self.buggy_clean_pairs.columns.tolist()
        commits_np = np.array_split(self.buggy_clean_pairs, self.cores)
        metrics_df = pd.DataFrame([])
        for i in range(2):
            # commit_df = pd.DataFrame(commits_np[i], columns = column_names)
            # commit_df.reset_index(inplace = True, drop = True)
            t = ThreadWithReturnValue(target = self.get_defective_pair_metrics, args = [commits_np[i]])
            threads.append(t)
        for th in threads:
            th.start()
        for th in threads:
            response = th.join()
            metrics_df = pd.concat([metrics_df,response])
            metrics_df.reset_index(inplace = True, drop = True)
        return metrics_df


    def clean_rows(self):
        """
        Remove duplicate rows
        """

        # Select columns which are considered for duplicate removal
        metric_cols = [
            col for col in self.metrics_dataframe.columns if not col in [
                "Name", "Bugs"]]

        # Drop duplicate rows
        self.deduped_metrics = self.metrics_dataframe.drop_duplicates(
            subset=metric_cols, keep=False)

        # Rearrange columns
        self.metrics_dataframe = self.metrics_dataframe[
            ["Name"]+metric_cols+["Bugs"]]

    def save_to_csv(self):
        """
        Save the metrics dataframe to CSV
        """
        # Determine the path to save file
        save_path = self.cwd.joinpath('datasets', self.repo_name+".csv")
        # Save the dataframe (no index column)
        self.metrics_dataframe.to_csv(save_path, index=False)

    def __exit__(self, exception_type, exception_value, traceback):
        """
        Actions to take on exit.

        Notes
        -----
        Go back up one level, and then remove the cloned repo. We're done here.
        """
        os.chdir(self.cwd)
        self._os_cmd("rm -rf {}/*und".format(self.udb_path))
        # Optional -- remove the clone repo to save some space.
        # self._os_cmd("rm -rf {}".format(self.source_path))
