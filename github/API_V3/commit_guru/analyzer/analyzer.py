"""
file: Analyzer.py
author: Christoffer Rosen <cbr4830@rit.edu>
date: November 2013
description: This module contains the functions for analyzing a repo with a given id.
Currently only supports the GitHub Issue Tracker.
"""
import sys
from datetime import datetime, timedelta
from commit_guru.analyzer.bugfinder import *
from commit_guru.analyzer.metricsgenerator import *
from commit_guru.analyzer.githubissuetracker import *
from commit_guru.caslogging import logging
from commit_guru.analyzer.notifier import *
from commit_guru.config import config
from commit_guru.analyzer.git_commit_linker import *
import pandas as pd
from os.path import dirname as up
import os

def analyze(repo_id):
	"""
	Analyze the repository with the given id. Gets the repository from the repository table
	and starts ingesting using the analyzeRepo method.
	@param repo_id		The repository id to analyze
	"""

	repo_to_analyze = [repo_id['name']]
	# Verify that repo exists
	if len(repo_to_analyze) > 0:
		analyzeRepo(repo_id)
	else:
		logging.info('Repo with id ' + repo_id['name'] + ' not found!')

def analyzeRepo(repository_to_analyze):
	"""
	Analyzes the given repository
	@param repository_to_analyze	The repository to analyze.
	@param session                  SQLAlchemy session
	@private
	"""
	repo_name = repository_to_analyze['name']

	logging.info('Worker analyzing repository  ' + repo_name)

	all_commits = pd.read_csv(up(os.path.dirname(__file__)) + '/Data/Commit/' + repo_name + '.csv')

	corrective_commits = all_commits[all_commits['fix'] == True]
	logging.info("Linking " + str(len(corrective_commits)) + " new corrective commits for repo " + repo_name)
	try:
		git_commit_linker = GitCommitLinker(repository_to_analyze)
		final_commits = git_commit_linker.linkCorrectiveCommits(corrective_commits, all_commits)
		#final_commits.to_csv(up(os.path.dirname(__file__)) + '/Data/commit_data/' + repo_name + '.csv',index=False)
    #print(os.getcwd())
		final_commits.to_csv('/home/smajumd3/Data_Miner/github/data/commit_guru/' + repo_name + '.csv',index=False)
    #final_commits.to_csv(up(up(up(up(up(up(os.getcwd())))))) + '/data/commit_guru/' + repo_name + '.csv',index=False)
	except Exception as e:
		logging.exception("Got an exception linking bug fixing changes to bug inducing changes for repo " + repo_name)
		# repository_to_analyze.status = "Error"
		# session.commit() # update repo status
		raise	
	logging.info("Linking done for repo" + repo_name)
