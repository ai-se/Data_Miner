"""
file: readRepo.py
authors: Ben Grawi <bjg1568@rit.edu>, Christoffer Rosen <cbr4830@rit.edu>
date: October 2013
description: This module contains the functions for ingesting a repository with
             a given id. 
"""
from commit_guru.caslogging import logging
import sys
from datetime import datetime, timedelta
from commit_guru.ingester.localrepository_file import *

def ingestRepo(repository_to_ingest):
  """
  Ingests a given repository
  @param repository_to_ingest   The repository to inspect
  @param session 				The SQLAlchemy session
  @private
  """
  logging.info( 'A worker is starting scan repository: ' +
                      repository_to_ingest['name'])
  local_repo = LocalRepository(repository_to_ingest)
  local_repo.sync()

  logging.info( 'A worker finished ingesting repo ' + 
                  repository_to_ingest['name'])


def ingest(repo_id):
  """
  Ingest a repository with the given id. Gets the repository information
  from the repository table and starts ingesting using ingestRepo method
  @param repo_id   The repository id to ingest.
  """
  repo_to_analyze = [repo_id['name']]
  # Verify that repo exists
  if len(repo_to_analyze) == 1:
    ingestRepo(repo_id)
  else:
    logging.info('Repo with id ' + repo_to_analyze + ' not found!')