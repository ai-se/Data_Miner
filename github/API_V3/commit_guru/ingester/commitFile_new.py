"""
Representing a single file in a commit
@name				name of file
@loc 				lines of code in file
@authors		 all authors of the file
@nuc				 number of unique changes made to the file
"""

class CommitFile:

	def __init__(self, name, loc, authors, lastchanged, owner,co_commited_files,adev):
		self.name = name												# File name
		self.loc = loc													# LOC in file
		self.authors = authors									# Array of authors
		self.lastchanged = lastchanged					# unix time stamp of when last changed
		self.nuc = 1
		self.owner = owner
		self.co_commited_files = co_commited_files
		self.adev = adev														# number of unique changes to the file
