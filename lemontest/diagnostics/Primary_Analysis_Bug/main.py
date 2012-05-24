#!/usr/bin/python

import sys, os, re, difflib

import json, pprint
pp = pprint.PrettyPrinter(indent=4)


zipDir = sys.argv[1]
tmpDir = sys.argv[2]
log = os.path.join(zipDir,'ReportLog.html')
stdout = os.path.join(zipDir,'drmaa_stdout.txt')


logFile = open(log,'r').read() 
logFile += open(stdout,'r').read()

#print logFile

#m = re.search(r".*Bus error|core dumped|Segmentation fault.*",logFile,re.S)
if 'Bus error'.lower() in logFile.lower() or 'core dumped'.lower() in logFile.lower() or 'Segmentation fault'.lower() in logFile.lower():
	print "Fail\n100\nThere is a major failure with the primary analysis code. Escalate!"

