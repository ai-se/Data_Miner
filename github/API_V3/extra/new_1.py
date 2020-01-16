# import understand as und
# import numpy
# from git_understand import git_understand
# from api import git_access,api_access
# from git_understand import git_understand as git_understand
# from git_log import git2repo
# import json
import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt
# import math
# import networkx as nx
# import re
# from git_log import git2data,git_commit_info,release_mine
# import threading
# from threading import Barrier
# from multiprocessing import Queue
# from os.path import dirname as up
import os
import shlex
import subprocess as sp
# import platform
# from commit_guru.cas_manager_v1 import *

print("its working")

df = pd.DataFrame([1,2,3,4,5,6,7])
df.to_csv('data.csv')

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

_os_cmd("ls -all", verbose=True)
_os_cmd("git clone https://github.com/docker-java/docker-java.git", verbose=True)