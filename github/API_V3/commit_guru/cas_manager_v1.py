"""
file: cas_manager.py
authors: Christoffer Rosen <cbr4830@rit.edu>
date: Jan. 2014
description: This module contains the CAS_manager class, which is a thread that continously checks if there
			 is work that needs to be done. Also contains supporting classes of Worker and ThreadPool used by
			 the CAS_Manager.
"""
from commit_guru.analyzer.analyzer import *
from commit_guru.ingester.ingester import *
#from orm.repository import *
import calendar # to convert datetime to unix time
from commit_guru.caslogging import logging
from queue import *
import threading
import time
import pandas as pd
import datetime
#from monthdelta import MonthDelta

class CAS_Manager(threading.Thread):
	""" 
	Thread that continiously checks if there is work to be done and adds it to
	the thread pool work queue
	"""

	def __init__(self,source_df):
		"""Constructor"""
		# threading.Thread.__init__(self)
		# numOfWorkers = 4
		# self.workQueue = ThreadPool(numOfWorkers)
		# self.modelQueue = Queue()
		# self.repos = pd.read_csv('repos.csv')
		self.repos = source_df
		self.repos = self.repos.replace({pd.np.nan: None})
		print(self.repos)

	def checkIngestion(self):
		"""Check if any repo needs to be ingested"""
		# repos_to_get = self.repos
		for i in range(self.repos.shape[0]):
			repo = self.repos.iloc[i]
			logging.info("Adding repo " + repo['name'] + " to work queue for ingesting")
			#self.workQueue.add_task(ingest,repo)
			ingest(repo)

		#session.close()

	def checkAnalyzation(self):
		"""Checks if any repo needs to be analyzed"""
		# repos_to_get = self.repos
		for i in range(self.repos.shape[0]):
			repo = self.repos.iloc[i]
			refresh_date = datetime.datetime.now() + datetime.timedelta(-30)
			print("========================",datetime.datetime.now(),refresh_date)
			if repo['last_analyzed'] is not None and repo['last_analyzed'] < refresh_date:
				continue
			logging.info("Adding repo " + repo['name']+ " to work queue for analyzing.")
			#self.workQueue.add_task(analyze, repo)
			analyze(repo)
			self.repos.loc[i,'last_analyzed'] = datetime.datetime.now()

	def run(self):

		self.checkIngestion()
		# self.workQueue.wait_completion()
		self.checkAnalyzation()
		# self.workQueue.wait_completion()
		# self.repos.to_csv('repos.csv',index=False)
		# while(True):
		# 	### --- Check repository table if there is any work to be done ---  ###
		# 	self.checkIngestion()
		# 	self.workQueue.wait_completion()
		# 	self.checkAnalyzation()
		# 	# self.checkModel()
		# 	# self.checkBuildModel()
		# 	time.sleep(10)
    
  def run_ingestion(self):
    self.checkIngestion()
