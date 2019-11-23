#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  5 18:54:29 2019

@author: suvodeepmajumder
"""
import codecs
import sys
import subprocess
import shlex
import json  # json is an easy way to send arbitrary ascii-safe lists of strings out of python
import sys

sys.path.append("..")
from git_log import git2repo
# from main.git_log import git2repo
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


# from main.utils.utils.utils import printProgressBar


def shell_split(cmd):
    if os.name == 'posix':
        return shlex.split(cmd)
    else:
        # TODO: write a version of this that doesn't invoke a subprocess
        if not cmd:
            return []
        # cmd = cmd.replace("\\\\", "\\")
        print("print cmd : ", cmd)
        full_cmd = '{} {}'.format(
            subprocess.list2cmdline([
                sys.executable, '-c',
                'import sys, json; print(json.dumps(sys.argv[1:]))'
            ]), cmd
        )
        ret = subprocess.check_output(full_cmd).decode()
        return json.loads(ret)


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

    def __init__(self, repo_url, repo_name, repo_lang):
        self.repo_url = repo_url
        self.repo_name = repo_name
        self.repo_lang = repo_lang
        self.repo_obj = git2repo.git2repo(self.repo_url, self.repo_name)
        self.repo = self.repo_obj.clone_repo()
        if platform.system() == 'Darwin' or platform.system() == 'Linux':
            self.repo_path = up(os.getcwd()) + '/temp_repo/' + self.repo_name
            self.file_path = up(os.getcwd()) + '/data/' + self.repo_name + '_commit.pkl'
            self.committed_file = up(os.getcwd()) + '/data/' + self.repo_name + '_committed_file.pkl'
        else:
            self.repo_path = up(os.getcwd()) + '\\temp_repo\\' + self.repo_name
            self.file_path = up(os.getcwd()) + '\\data\\' + self.repo_name + '_commit.pkl'
            self.committed_file = up(os.getcwd()) + '\\data\\' + self.repo_name + '_committed_file.pkl'
        self.buggy_clean_pairs = self.read_commits()
        print("generated buggy clean pairs")
        self.repo_path = self.repo_obj.repo_path
        # Reference current directory, so we can go back after we are done.
        self.cwd = Path(os.getcwd())

        # Generate path to store udb files
        self.udb_path = self.cwd.joinpath(".temp", "udb")

        # Create a folder to hold the udb files
        if not self.udb_path.is_dir():
            os.makedirs(self.udb_path)

        # Generate source path where the source file exist
        self.source_path = self.cwd.joinpath(
            ".temp", "sources", self.repo_name)
        print(self.source_path)

    def read_commits(self):
        print(self.file_path)
        df = pd.read_pickle(self.file_path)
        df_committed_file = pd.read_pickle(self.committed_file)
        df = df[df['buggy'] == 1]
        df_commits = df.drop(labels=['message', 'buggy'], axis=1)
        commits = []
        temp = df_commits.shape[0]
        print("here are they :", temp)
        for i in range(df_commits.shape[0]):
            committed_files = []
            if df_commits.iloc[i, 0] == None or df_commits.iloc[i, 1] == None:
                continue
            # print("printing row of commits : \n", df_commits.iloc[i,1])
            bug_fixing_commit = self.repo.get(df_commits.iloc[i, 0])
            bug_existing_commit = self.repo.get(df_commits.iloc[i, 1])
            if bug_fixing_commit == None:
                print(df_commits.iloc[i, 0])
                continue
            for index, row in df_committed_file[df_committed_file['commit_id'] == df_commits.iloc[i, 0]].iterrows():
                a = row['file_path']
#                if len(row['file_path'].split('/')) == 1:
#                    print("3")
#                    continue
                committed_files.append(row['file_path'].replace('/', '.').rsplit('.', 1)[0])
            commits.append([bug_existing_commit, bug_fixing_commit, committed_files])
        return commits

    @staticmethod
    def _os_cmd(cmd, verbose=True):
        """
        Run a command on the shell

        Parameters
        ----------
        cmd: str
            A command to run.
        """
        # print("string : ", cmd)
        cmd = shell_split(cmd)
        # cmd = shlex.split(cmd)
        with sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.DEVNULL) as p:
            out, err = p.communicate()

        if verbose:
            print(out)
            print(err)
        return out, err

    def _create_und_files(self, file_name_suffix):
        """
        Creates understand project files
        Parameters
        ----------
        file_name_suffix : str
            A suffix for the understand_filenames
        """
        # Create a handle for storing *.udb file for the project
        und_file = self.udb_path.joinpath(
            "{}_{}.udb".format(self.repo_name, file_name_suffix))
        # Go to the udb path
        os.chdir(self.udb_path)

        # find and replace all F90 to f90
        for filename in glob(os.path.join(self.repo_path, '*/**')):
            if ".F90" in filename:
                os.rename(filename, filename[:-4] + '.f90')

        # Generate udb file
        if self.repo_lang == "fortran":
            cmd = "und create -languages Fortran add {} analyze {}".format(
                str(self.repo_path), str(und_file))
        elif self.repo_lang == "python":
            cmd = "und create -languages python add {} analyze {}".format(
                str(self.repo_path), str(und_file))
        elif self.repo_lang == "C":
            cmd = "und create -languages C++ add {} analyze {}".format(
                str(self.repo_path), str(und_file))
        elif self.repo_lang == "java":
            cmd = "und create -languages Java add {} analyze {}".format(
                str(self.repo_path), str(und_file))
        out, err = self._os_cmd(cmd)

        if file_name_suffix == "buggy":
            self.buggy_und_file = und_file
        elif file_name_suffix == "clean":
            self.clean_und_file = und_file

        # Go to the cloned repo
        os.chdir(self.repo_path)

    def _files_changed_in_git_diff(self, hash_1, hash_2):
        """
        Get a list of all the files changed between two hashes

        Parameters
        ----------
        hash_1 : str
            Commit hash 1.
        hash_2 : bool
            Commit hash 2.

        Returns
        -------
        List[str]:
            A list of all files changed. For simplicity we only include *.py
            *.F90, *.c, *.cpp, *.java.
        """

        os.chdir(self.repo_path)
        out, __ = self._os_cmd(
            "git diff {} {} --name-only".format(hash_1.id.hex, hash_2.id.hex))
        files_changed = []
        for file in out.splitlines():
            for wanted in [".py", ".c", ".cpp", ".F90", ".f90", ".java"]:
                if wanted in str(file) and "__init__.py" not in str(file):
                    files_changed.append(Path(str(file)).name[:-1])

        # A work around for FORTRAN file extensions.
        if self.repo_lang == "fortran":
            files_changed = list(map(lambda x: x[:-4] + ".f90", files_changed))

        return files_changed

    def get_all_metrics(self):
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

        self.metrics_dataframe = pd.DataFrame()

        # printProgressBar(0, len(self.buggy_clean_pairs), prefix='Progress:',
        #                 suffix='Complete', length=50)

        # 1. For each clean-buggy commit pairs
        print(len(self.buggy_clean_pairs))
        for i in range(len(self.buggy_clean_pairs)):
            buggy_hash = self.buggy_clean_pairs[i][0]
            clean_hash = self.buggy_clean_pairs[i][1]
            files_changed = self.buggy_clean_pairs[i][2]
            if len(files_changed) == 0:
                continue
            print(i, (buggy_hash.id.hex, clean_hash.id.hex))
            print("---------FILES CHANGED---------", files_changed)
            # Go the the cloned project path
            os.chdir(self.repo_path)
            # print(self.repo_path)
            # Checkout the master branch first, we'll need this
            # to find what files have changed.
            self._os_cmd("git reset --hard master", verbose=False)

            # Get a list of files changed between the two hashes
            # files_changed = self._files_changed_in_git_diff(
            #    buggy_hash, clean_hash)
            # ------------------------------------------------------------------
            # ---------------------- BUGGY FILES METRICS -----------------------
            # ------------------------------------------------------------------
            # Checkout the buggy commit hash
            self._os_cmd(
                "git reset --hard {}".format(buggy_hash.id.hex), verbose=False)

            # Create a understand file for this hash
            self._create_und_files("buggy")
            # print(self.buggy_und_file)
            db_buggy = und.open(str(self.buggy_und_file))
            print(len(db_buggy.ents("Class")))
            temp = db_buggy.ents("File")
            for file in db_buggy.ents("Class"):
                # print directory name
                if file.library() == "Standard":
                    continue
                t3 = file.longname()
                t7 = file.refs()
                t8 = file.ref()
                #print("-------Here is the library : ",file.library())
                #r = re.compile(str(file.longname()))
                temp_str = file.longname().split(".")[-2]
                r = re.compile(str(temp_str))
                newlist = list(filter(r.search, list(set(files_changed))))
                if len(newlist) > 0:
                    #print("Files changed, newList, r ",files_changed, newlist, r)
                    metrics = file.metric(file.metrics())
                    metrics["Name"] = file.longname()
                    metrics["Bugs"] = 1
                    self.metrics_dataframe = self.metrics_dataframe.append(
                        pd.Series(metrics), ignore_index=True)
            # Purge und file
            db_buggy.close()
            # self._os_cmd("rm {}".format(str(self.buggy_und_file)))
            os.remove(str(self.buggy_und_file))

            # ------------------------------------------------------------------
            # ---------------------- CLEAN FILES METRICS -----------------------
            # ------------------------------------------------------------------
            # Checkout the clean commit hash
            self._os_cmd(
                "git reset --hard {}".format(clean_hash.id.hex), verbose=False)

            # Create a understand file for this hash
            self._create_und_files("clean")
            db_clean = und.open(str(self.clean_und_file))
            for file in db_clean.ents("Class"):
                # print directory name
                #r = re.compile(str(file.longname()))
                if file.library() == "Standard":
                    continue
                temp_str = file.longname().split(".")[-2]
                r = re.compile(str(temp_str))
                newlist = list(filter(r.search, files_changed))
                if len(newlist) > 0:
                    metrics = file.metric(file.metrics())
                    # print(metrics)
                    metrics["Name"] = file.name()
                    metrics["Bugs"] = 0
                    self.metrics_dataframe = self.metrics_dataframe.append(
                        pd.Series(metrics), ignore_index=True)
            db_clean.close()
            # Purge und file
            # self._os_cmd("rm {}".format(str(self.clean_und_file)))
            os.remove(str(self.clean_und_file))
            print(self.metrics_dataframe)

            # printProgressBar(i, len(self.buggy_clean_pairs),
            #                 prefix='Progress:', suffix='Complete', length=50)
        return self.metrics_dataframe

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
            ["Name"] + metric_cols + ["Bugs"]]

    def save_to_csv(self):
        """
        Save the metrics dataframe to CSV
        """
        # Determine the path to save file
        save_path = self.cwd.joinpath('datasets', self.repo_name + ".csv")
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

obj = MetricsGetter("https://github.com/trentm/python-markdown2", "python-markdown2", "python")
ans = obj.get_all_metrics()
print("Done with metrics")

