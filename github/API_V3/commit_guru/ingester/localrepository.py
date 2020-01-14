"""
file: localrepository.py
author: Ben Grawi <bjg1568@rit.edu>
date: October 2013
description: Holds the repository abstraction class
"""
from commit_guru.ingester.git import *
#from orm.commit import *
from datetime import datetime
import os
import logging
import pandas as pd
from os.path import dirname as up

class LocalRepository():
    """
    Repository():
    description: Abstracts the actions done on a repository
    """
    repo = None
    adapter = None
    start_date = None
    def __init__(self, repo):
        """
        __init__(path): String -> NoneType
        description: Abstracts the actions done on a repository
        """
        self.repo = repo
        print("The repo is:",self.repo['name'])

        # Temporary until other Repo types are added
        self.adapter = Git

        self.commits = {}

    def sync(self):
        """
        sync():
        description: Simply wraps the syncing functions together
        """

        # TODO: Error checking.
        firstSync = self.syncRepoFiles()
        self.syncCommits(firstSync)

        # Set the date AFTER it has been ingested and synced.
        self.repo.ingestion_date = self.start_date

    def syncRepoFiles(self):
        """
        syncRepoFiles() -> Boolean
        description: Downloads the current repo locally, and sets the path and
            injestion date accordingly
        returns: Boolean - if this is the first sync
        """
        # Cache the start date to set later
        self.start_date = str(datetime.now().replace(microsecond=0))

        path = os.path.dirname(__file__) + self.adapter.REPO_DIRECTORY + self.repo['name']
        # See if repo has already been downloaded, if it is pull, if not clone
        print("This is the current path:",path)
        if os.path.isdir(path):
            self.adapter.pull(self.adapter, self.repo)
            firstSync = False
        else:
            self.adapter.clone(self.adapter, self.repo)
            firstSync = True

        return firstSync

    def syncCommits(self, firstSync):
        """
        syncCommits():
        description: Makes each commit dictonary into an object and then
            inserts them into the database
        arguments: firstSync Boolean: whether to sync all commits or after the
            ingestion date
        """
        commits = self.adapter.log(self.adapter, self.repo, firstSync)
        commit_df = pd.DataFrame(commits)
        
        # commitsSession = Session()
        logging.info('Saving commits to the csv...')
        commit_df.to_csv(up(os.path.dirname(__file__)) + '/Data/Commit/' + self.repo['name'] + '.csv',index=False)
        # for commitDict in commits:
        #     commitDict['repository_id'] = self.repo
        #     commitsSession.merge(Commit(commitDict))
        # commitsSession.commit()
        # commitsSession.close()
        logging.info('Done saving commits to the csv.')
