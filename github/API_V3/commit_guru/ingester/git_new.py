import os
import subprocess
import json
import logging
import math                               # Required for the math.log function
from commit_guru.ingester.commitFile_new import *         # Represents a file
from commit_guru.classifier.classifier import *       # Used for classifying each commit
import time
import pandas as pd

"""
file: repository.py
authors: Ben Grawi <bjg1568@rit.edu>, Christoffer Rosen <cbr4830@rit.edu>
date: October 2013
description: Holds the repository git abstraction class
"""

class Git():
    """
    Git():
    pre-conditions: git is in the current PATH
                    self.path is set in a parent class
    description: a very basic abstraction for using git in python.
    """
    # Two backslashes to allow one backslash to be passed in the command.
    # This is given as a command line option to git for formatting output.

    # A commit mesasge in git is done such that first line is treated as the subject,
    # and the rest is treated as the message. We combine them under field commit_message

    # We want the log in ascending order, so we call --reverse
    # Numstat is used to get statistics for each commit
    LOG_FORMAT = '--pretty=format:\" CAS_READER_STARTPRETTY\
    \\"parent_hashes\\"CAS_READER_PROP_DELIMITER: \\"%P\\",CAS_READER_PROP_DELIMITER2\
    \\"commit_hash\\"CAS_READER_PROP_DELIMITER: \\"%H\\",CAS_READER_PROP_DELIMITER2\
    \\"author_name\\"CAS_READER_PROP_DELIMITER: \\"%an\\",CAS_READER_PROP_DELIMITER2\
    \\"author_email\\"CAS_READER_PROP_DELIMITER: \\"%ae\\",CAS_READER_PROP_DELIMITER2\
    \\"author_date\\"CAS_READER_PROP_DELIMITER: \\"%ad\\",CAS_READER_PROP_DELIMITER2\
    \\"author_date_unix_timestamp\\"CAS_READER_PROP_DELIMITER: \\"%at\\",CAS_READER_PROP_DELIMITER2\
    \\"commit_message\\"CAS_READER_PROP_DELIMITER: \\"%s%b\\"\
    CAS_READER_STOPPRETTY \" --numstat --reverse '

    CLONE_CMD = 'git clone {!s} {!s}'     # git clone command w/o downloading src code
    PULL_CMD = 'git pull'      # git pull command
    RESET_CMD = 'git reset --hard FETCH_HEAD'
    CLEAN_CMD = 'git clean -df' # f for force clean, d for untracked directories

    REPO_DIRECTORY = "/CASRepos/git/"        # directory in which to store repositories

    def getCommitStatsProperties( stats, commitFiles, devExperience, author, unixTimeStamp, _commit_hash):
        """
        getCommitStatsProperties
        Helper method for log. Caclulates statistics for each change/commit and
        returns them as a comma seperated string. Log will add these to the commit object
        properties

        @param stats            These are the stats given by --numstat as an array
        @param commitFiles      These are all tracked commit files
        @param devExperience    These are all tracked developer experiences
        @param author           The author of the commit
        @param unixTimeStamp    Time of the commit
        """
        all_files = []

        statProperties = ""

        # Data structures to keep track of info needed for stats
        subsystemsSeen = []                         # List of system names seen
        directoriesSeen = []                        # List of directory names seen
        locModifiedPerFile = []                     # List of modified loc in each file seen
        authors = []                                # List of all unique authors seen for each file
        fileAges = []                               # List of the ages for each file in a commit

        # Stats variables
        la = 0                                      # lines added - done
        ld = 0                                      # lines deleted -done
        nf = 0                                      # Number of modified files
        ns = 0                                      # Number of modified subsystems - done
        nd = 0                                      # number of modified directories - done
        entrophy = 0                                # entrophy: distriubtion of modified code across each file
        lt = 0                                      # lines of code in each file (sum) before the commit - done
        ndev = 0                                    # the number of developers that modifed the files in a commit - done
        age = 0                                     # the average time interval between the last and current change -done
        exp = 0                                     # number of changes made by author previously - done
        rexp = 0                                    # experience weighted by age of files ( 1 / (n + 1)) -done
        sexp = 0                                    # changes made previous by author in same subsystem - done
        totalLOCModified = 0                        # Total modified LOC across all files
        nuc = 0                                     # number of unique changes to the files - done
        filesSeen = ""                              # files seen in change/commit 
        # print("++++++++++++++++++++++++++")
        for stat in stats:
            x = []
            file_auth = []
            file_subsystemsSeen = []
            file_directoriesSeen = []
            minor = 0
            co_commited_files = {}
            nadev = 0
            ncomm = 0
            num_files = 0

            if( stat == ' ' or stat == '' ):
                continue

            fileStat = stat.split("\\t")

            # Check that we are only looking at file stat (i.e., remove extra newlines)
            if( len(fileStat) < 2):
                continue

            # catch the git "-" line changes
            try:
                fileLa = int(fileStat[0])
                fileLd = int(fileStat[1])
            except:
                fileLa = 0
                fileLd = 0

            # Remove oddities in filename so we can process it
            fileName = (fileStat[2].replace("'",'').replace('"','').replace("\\",""))


            totalModified = fileLa + fileLd

            x.append(_commit_hash)
            # have we seen this file already?
            if(fileName in commitFiles):
                prevFileChanged = commitFiles[fileName]
                prevLOC = getattr(prevFileChanged, 'loc')
                prevAuthors = getattr(prevFileChanged, 'authors')
                prevChanged = getattr(prevFileChanged, 'lastchanged')
                file_nuc = getattr(prevFileChanged, 'nuc')
                owner = getattr(prevFileChanged, 'owner')
                co_commited_files = getattr(prevFileChanged, 'co_commited_files')
                nuc += file_nuc
                lt += prevLOC

                for prevAuthor in prevAuthors:
                    if prevAuthor not in authors:
                        authors.append(prevAuthor)
                    if prevAuthor not in file_auth:
                        file_auth.append(prevAuthor)

                # Convert age to days instead of seconds
                age += ( (int(unixTimeStamp) - int(prevChanged)) / 86400 )
                fileAges.append(prevChanged)

                # update owner
                if author not in owner:
                    owner.update({author:fileLa})
                else:
                    owner[author] += fileLa
                # update committed files and calculating ndev
                for stat in stats:
                    if( stat == ' ' or stat == '' ):
                        continue
                    fileStat = stat.split("\\t")
                    committed_fileName = (fileStat[2].replace("'",'').replace('"','').replace("\\",""))
                    if committed_fileName != fileName:
                        if committed_fileName not in co_commited_files.keys():
                            co_commited_files.update({committed_fileName:1})
                            num_files += 1
                            if committed_fileName not in commitFiles.keys():
                                nadev += 1*1
                                ncomm += 1*1
                            else:
                                nadev += len(getattr(commitFiles[committed_fileName], 'authors'))*1
                                ncomm += getattr(commitFiles[committed_fileName], 'nuc')*1
                        else:
                            co_commited_files[committed_fileName] += 1
                            num_files += 1
                            if committed_fileName not in commitFiles.keys():
                                nadev += 1*co_commited_files[committed_fileName]
                                ncomm += 1*co_commited_files[committed_fileName]
                            else:
                                nadev += len(getattr(commitFiles[committed_fileName], 'authors'))*co_commited_files[committed_fileName]
                                ncomm += getattr(commitFiles[committed_fileName], 'nuc')*co_commited_files[committed_fileName]

                # if num_files == 0:
                #     nadev = 0
                # else:
                #     nadev = nadev/num_files


                # Update the file info

                file_nuc += 1 # file was modified in this commit
                setattr(prevFileChanged, 'loc', prevLOC + fileLa - fileLd)
                setattr(prevFileChanged, 'authors', authors)
                setattr(prevFileChanged, 'lastchanged', unixTimeStamp)
                setattr(prevFileChanged, 'nuc', file_nuc)
                setattr(prevFileChanged, 'owner', owner)
                setattr(prevFileChanged, 'co_commited_files', co_commited_files)


                # calculate OWN
                if sum(owner.values()) != 0:
                    own = max(owner.values())/sum(owner.values())
                else:
                    own = 0

                # calculate MINOR
                for key in owner:
                    if owner[key] <= 0.05*sum(owner.values()):
                        minor += 1

                


                x.append(fileName) # file name
                x.append(fileLa) # lines added
                x.append(fileLd) # lines deleted
                x.append(prevLOC) # lines of code before commit
                x.append(((int(unixTimeStamp) - int(prevChanged)) / 86400 )) # the average time interval between the last and current change
                x.append(len(file_auth)) # the number of developers that modifed the files in a commit
                x.append(file_nuc) # number of unique changes to the files
                x.append(own) # measures the percentage of the lines authored by the highest contributor of a file
                x.append(minor) # measures the number of contributors who authored less than 5%
                x.append(nadev) # numder of developer committed weighied by number of time they were committed
                x.append(ncomm) # numder of neighbouring commits weighied by number of time they were committed


            else:

                # new file we haven't seen b4, add it to file commit files dict
                if(author not in authors):
                    authors.append(author)
                
                if(author not in file_auth):
                    file_auth.append(author)

                if(unixTimeStamp not in fileAges):
                    fileAges.append(unixTimeStamp)
                
                # update committed files and calculating ndev
                for stat in stats:
                    if( stat == ' ' or stat == '' ):
                        continue
                    fileStat = stat.split("\\t")
                    committed_fileName = (fileStat[2].replace("'",'').replace('"','').replace("\\",""))
                    if committed_fileName != fileName:
                        if committed_fileName not in co_commited_files.keys():
                            co_commited_files[committed_fileName] = 1
                            num_files += 1
                            nadev += 1*1
                            ncomm += 1*1

                # if num_files == 0:
                #     nadev = 0
                # else:
                #     nadev = nadev/num_files
                # print(co_commited_files)

                fileObject = CommitFile(fileName, fileLa - fileLd, authors, unixTimeStamp, {author:fileLa},co_commited_files)
                commitFiles[fileName] = fileObject



                x.append(fileName) # file name
                x.append(fileLa) # lines added
                x.append(fileLd) # lines deleted
                x.append(0) # lines of code before commit
                x.append(0) # the average time interval between the last and current change
                x.append(len(file_auth)) # the number of developers that modifed the files in a commit
                x.append(0) # number of unique changes to the files
                x.append(1) # measures the percentage of the lines authored by the highest contributor of a file
                x.append(0) # measures the number of contributors who authored less than 5%
                x.append(nadev) # numder of developer committed weighied by number of time they were committed
                x.append(ncomm) # numder of neighbouring commits weighied by number of time they were committed

            # end of stats loop


            locModifiedPerFile.append(totalModified) # Required for entrophy
            totalLOCModified += totalModified
            fileDirs = fileName.split("/")

            if( len(fileDirs) == 1 ):
                subsystem = "root"
                directory = "root"
            else:
                subsystem = fileDirs[0]
                directory = "/".join(fileDirs[0:-1])

            if( subsystem not in file_subsystemsSeen ):
                file_subsystemsSeen.append( subsystem ) 
            
            x.append(len(file_subsystemsSeen)) # number of subsystem
 
            if( subsystem not in subsystemsSeen ):
                subsystemsSeen.append( subsystem ) 

            if( author in devExperience ):
                experiences = devExperience[author]
                exp += sum(experiences.values())

                x.append(sum(experiences.values()))  # number of changes made by author previously

                if( subsystem in experiences ):
                    sexp = experiences[subsystem]
                    experiences[subsystem] += 1
                else:
                    experiences[subsystem] = 1

                x.append(sexp) # changes made previous by author in same subsystem

                try:
                    rexp += (1 / (age) + 1)
                    x.append((1 / (age) + 1)) # experience weighted by age of files ( 1 / (n + 1))
                except:
                    rexp += 0
                    x.append(0)
                
            else:
                devExperience[author] = {subsystem: 1}

            if( directory not in directoriesSeen ):
                directoriesSeen.append( directory )
            
            if( directory not in file_directoriesSeen ):
                file_directoriesSeen.append( directory)
            
            x.append(len(file_directoriesSeen)) # number of directories

            # Update file-level metrics
            la += fileLa
            ld += fileLd
            nf += 1
            filesSeen += fileName + ",CAS_DELIMITER,"
            all_files.append(x)    
        # End stats loop

        if( nf < 1):
            return "",""

        # Update commit-level metrics
        ns = len(subsystemsSeen)
        nd = len(directoriesSeen)
        ndev = len(authors)
        lt = lt / nf
        age = age / nf
        exp = exp / nf
        rexp = rexp / nf


        # Update entrophy
        for file_num in range(len(locModifiedPerFile)):
            fileLocMod = locModifiedPerFile[file_num]
            if (fileLocMod != 0 ):
                avg = fileLocMod/totalLOCModified
                ind_entropy = ( avg * math.log( avg,2 ) )
                all_files[file_num].append(ind_entropy)
                entrophy -= ind_entropy

        # Add stat properties to the commit object
        statProperties += ',"la":"' + str( la ) + '\"'
        statProperties += ',"ld":"' + str( ld ) + '\"'
        statProperties += ',"fileschanged":"' + filesSeen[0:-1] + '\"'
        statProperties += ',"nf":"' + str( nf ) + '\"'
        statProperties += ',"ns":"' + str( ns ) + '\"'
        statProperties += ',"nd":"' + str( nd ) + '\"'
        statProperties += ',"entrophy":"' + str(  entrophy ) + '\"'
        statProperties += ',"ndev":"' + str( ndev ) + '\"'
        statProperties += ',"lt":"' + str( lt ) + '\"'
        statProperties += ',"nuc":"' + str( nuc ) + '\"'
        statProperties += ',"age":"' + str( age ) + '\"'
        statProperties += ',"exp":"' + str( exp ) + '\"'
        statProperties += ',"rexp":"' + str( rexp ) + '\"'
        statProperties += ',"sexp":"' + str( sexp ) + '\"'
        # print("+++++++++++++++++++++++++++++++++++++++")
        # print("+++++++++++++++++++++++++++++++++++++++")
        # print("+++++++++++++++++++++++++++++++++++++++")
        # print("+++++++++++++++++++++++++++++++++++++++")
        # print("+++++++++++++++++++++++++++++++++++++++")
        # print("+++++++++++++++++++++++++++++++++++++++")
        # print("+++++++++++++++++++++++++++++++++++++++")
        # print(all_files)
        # print(statProperties, all_files)
        return (statProperties, all_files)
    # End stats

    def log(self, repo, firstSync):
        """
        log(): Repository, Boolean -> Dictionary
        arguments: repo Repository: the repository to clone
                   firstSync Boolean: whether to sync all commits or after the
            ingestion date
        description: a very basic abstraction for using git in python.
        """
        repo_dir = os.chdir(os.path.dirname(__file__) + self.REPO_DIRECTORY + repo['name'])
        logging.info('Getting/parsing git commits: '+ str(repo['name']) )

        # Spawn a git process and convert the output to a string
        # if not firstSync and repo.ingestion_date is not None:
        #     cmd = 'git log --after="' + repo.ingestion_date + '" '
        # else:
        cmd = 'git log '

        log = str( subprocess.check_output(cmd + self.LOG_FORMAT, shell=True, cwd = repo_dir ) )
        log = log[2:-1]   # Remove head/end clutter

        # List of json objects
        json_list = []

        # Make sure there are commits to parse
        if len(log) == 0:
            return []

        commitFiles = {}            # keep track of ALL file changes
        devExperience = {}          # Keep track of ALL developer experience
        classifier = Classifier()   # classifier for classifying commits (i.e., corrective, feature addition, etc)

        commitList = log.split("CAS_READER_STARTPRETTY")
        all_commits = []
        for commit in commitList:
            author = ""                                 # author of commit
            unixTimeStamp = 0                           # timestamp of commit
            fix = False                                 # whether or not the change is a defect fix
            classification = None                       # classification of the commit (i.e., corrective, feature addition, etc)
            isMerge = False                             # whether or not the change is a merge
            _commit_hash = None
            commit = commit.replace('\\x', '\\u00')   # Remove invalid json escape characters
            splitCommitStat = commit.split("CAS_READER_STOPPRETTY")  # split the commit info and its stats

            # The first split will contain an empty list
            if(len(splitCommitStat) < 2):
                continue

            prettyCommit = splitCommitStat[0]
            statCommit = splitCommitStat[1]
            commitObject = ""

            # Start with the commit info (i.e., commit hash, author, date, subject, etc)
            prettyInfo = prettyCommit.split(',CAS_READER_PROP_DELIMITER2    "')
            for propValue in prettyInfo:
                props = propValue.split('"CAS_READER_PROP_DELIMITER: "')
                propStr = ''
                if props[0] == 'commit_hash':
                    _commit_hash = props[1]
                for prop in props:
                    prop = prop.replace('\\','').replace("\\n", '')  # avoid escapes & newlines for JSON formatting
                    propStr = propStr + '"' + prop.replace('"','') + '":'

                values = propStr[0:-1].split(":")

                if(values[0] == '"    parent_hashes"'):
                    # Check to see if this is a merge change. Fix for Issue #26. 
                    # Detects merges by counting the # of parent commits
                    
                    parents = values[1].split(' ')
                    if len(parents) == 2:
                        isMerge = True

                if(values[0] == '"author_name"'):
                    author = values[1].replace('"', '')

                if(values[0] == '"author_date_unix_timestamp"'):
                    unixTimeStamp = values[1].replace('"','')

                # Classify the commit
                if(values[0] == '"commit_message"'):

                    if (isMerge):
                        classification = "Merge"
                    else:
                        classification = classifier.categorize(values[1].lower())

                    # If it is a corrective commit, we induce it fixes a bug somewhere in the system
                    if classification == "Corrective":
                        fix = True


                commitObject += "," + propStr[0:-1]
                # End property loop
            # End pretty info loop
            # print(commitObject)

            # Get the stat properties
            stats = statCommit.split("\\n")
            obj = self.getCommitStatsProperties(stats, commitFiles, devExperience, author, unixTimeStamp,_commit_hash)
            commitObject += obj[0]
            all_commits.append(obj[1])
            # Update the classification of the commit
            commitObject += ',"classification":"' + str( classification ) + '\"'

             # Update whether commit was a fix or not
            commitObject += ',"fix":"' + str( fix ) + '\"'

            # Remove first comma and extra space
            commitObject = commitObject[1:].replace('    ','')

            # Add commit object to json_list
            json_list.append(json.loads('{' + commitObject + '}'))
        # print(commitFiles)
        # End commit loop
        # print(all_commits)
        all_commits_list = [item for sublist in all_commits for item in sublist]
        all_commit_df = pd.DataFrame(all_commits_list,columns=['commit_hash','file_name','la','ld','lt','age','ndev','nuc','own','minor','ndev','ncomm','ns','exp','sexp','rexp','nd','sctr'])
        all_commit_df.to_csv('//Users/suvodeepmajumder/Documents/AI4SE/Data_Miner/github/data/commit_guru_exp/' + str(repo['name']) + '_file.csv',index=False)
        # all_commit_df.to_csv('/home/smajumd3/Data_Miner/github/data/commit_guru_new/' + str(repo['name']) + '_file.csv',index=False)
        logging.info('Done getting/parsing git commits.')
        return json_list

    def clone(self, repo):
        """
        clone(repo): Repository -> String
        description:Takes the current repo and clones it into the
            `clone_directory/the_repo_id`
        arguments: repo Repository: the repository to clone
        pre-conditions: The repo has not been already created
        """
        repo_dir = os.chdir(os.path.dirname(__file__) + self.REPO_DIRECTORY)

        # Run the clone command and return the results

        logging.info('Git cloning repo: '+ str(repo['name']) )
        cloneResult = str(subprocess.check_output(
                  self.CLONE_CMD.format(repo['url'], './' + repo['name']),
                  shell= True,
                  cwd = repo_dir ) )
        logging.info('Done cloning.')
        #logging.debug("Git clone result:\n" + cloneResult)

        # Reset path for next repo

        # TODO: only return true on success, else return false
        return True

    def pull(self, repo):
        """
        fetch(repo): Repository -> String
        description:Takes the current repo and pulls the latest changes.
        arguments: repo Repository: the repository to pull
        pre-conditions: The repo has already been created
        """
        print('working on pulling')
        repo_dir = os.path.dirname(__file__) + self.REPO_DIRECTORY + repo['name']

        # Weird sceneario where something in repo gets modified - reset all changes before pulling
        subprocess.call(self.RESET_CMD, shell=True, cwd= repo_dir)
        subprocess.call(self.CLEAN_CMD, shell=True, cwd= repo_dir)

        # Run the pull command and return the results
        logging.info('Pulling latest changes from repo: '+ str(repo['name']) )
        fetchResult = str(subprocess.check_output(
                  self.RESET_CMD + "\n" + self.PULL_CMD ,
                  shell=True,
                  cwd=  repo_dir  ) )
        logging.info('Done fetching.')
        #logging.debug("Git pull result:\n" + cloneResult)

        # TODO: only return true on success, else return false
        return True
