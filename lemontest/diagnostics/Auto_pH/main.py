#!/usr/bin/env python
import sys
import time
import datetime
import re

class InitLog:
	"Auto pH performance data from InitLog*.txt"
	def __init__(self):
		self.fileName = ""
		self.instName = ""
		self.dates    = []
		self.midSteps = []
		self.endSteps = []
		self.aborted  = False
		self.missing  = True
		self.issues   = ""
		self.outcome  = "Alerted"
	
def main():
	archive_path = "."
	output_path  = "."
	
	try:
		archive_path = sys.argv[1]
		output_path  = sys.argv[2]
	except IndexError:
		pass

	outputStatus = "N/A"
	outputPriority = 0
	runNumber = 1
	with open(output_path + "/results.html", 'w') as f:
		files=['InitLog.txt',
			'missing.txt',
			'InitLog1.txt',
			'InitLog2.txt']

		for afile in files:
			log = readInitLog(archive_path + "/" + afile)

			if runNumber == 1: 
				if "Passed" in log.outcome:
					outputStatus = "OK"
					outputPriority = 10
				else:
					outputStatus = "Alert"
					outputPriority = 40

				print outputStatus
				print outputPriority
				print "Most recent Auto pH run " + log.outcome
				writeOutputPreamble(f, log.instName);

			runNumber = printRun(log, runNumber, f)

		writeOutputPostscript(f)

def printRun(log, runNumber, f):
	if not log.missing:
		f.write("<tr>\n")
		f.write("<td style=\"vertical-align:middle\">" + str(runNumber) + "</td>\n")
		
		if "Passed" in log.outcome:
			f.write("<td style=\"vertical-align:middle\" class=\"phPass\">" + log.outcome + "</td>\n")
		elif "Alerted" in log.outcome:
			f.write("<td style=\"vertical-align:middle\" class=\"phAlert\">" + log.outcome + "</td>\n")
		else:
			f.write("<td style=\"vertical-align:middle\">" + log.outcome + "</td>\n")

		# TODO split issues with br
		f.write("<td style=\"vertical-align:middle\">" + log.issues + "</td>\n")

		try:
			startDate = log.dates[0]
			endDate   = log.dates[1]
			duration  = endDate - startDate
			printTiming(f, startDate, endDate, duration)
		except IndexError:
			pass

		if len(log.midSteps) > len(log.endSteps):
			printMiddleIterations(f, log.midSteps)
			printTotalW1(f, log.midSteps, 2)
		else:
			printFinalIterations(f, log.endSteps)
			printTotalW1(f, log.endSteps, 3)
		f.write("</tr>\n")

		runNumber += 1

	return runNumber

def printTiming(f,startDate, endDate, duration):
	heredoc = """<td>
<table class="table table-stripe2">
<thead>
<tr><th>&nbsp;</th><th></th></tr>
</thead>
<tbody>
<tr><td>Start</td><td>{start}</td></tr>
<tr><td>Stop</td><td>{stop}</td></tr>
<tr><td>Duration</td><td>{duration}</td></tr>
</tbody>
</table>
</td>
"""
	f.write(heredoc.format(start=startDate.strftime("%Y-%m-%d %H:%M:%S"), 
						   stop=endDate.strftime("%Y-%m-%d %H:%M:%S"),
						   duration=str(duration)))

def printMiddleIterations(f, steps):
	if len(steps) == 0:
		f.write("<td>No Iterations</td>\n")
	else:
		heredoc = """<td>
<table class="table table-stripe2">
<thead>
<tr><th>Step</th><th>End pH</th><th>W1 added</th></tr>
</thead>
<tbody>
"""
		f.write(heredoc)
	
		try:
			for step in steps:
				f.write("<tr><td>" + str(step[0]) + "</td><td>" + str(step[1]) + "</td><td>" + str(step[2]) + "</td></tr>\n")
		except IndexError:
			pass

		heredoc = """</tbody>
</table>
</td>
"""
		f.write(heredoc)

def printFinalIterations(f, steps):
	if len(steps) == 0:
		f.write("<td>No Iterations</td>\n")
	else:
		heredoc = """<td>
<table class="table table-stripe2">
<thead>
<tr><th>Step</th><th>Start pH</th><th>End pH</th><th>W1 added</th></tr>
</thead>
<tbody>
"""
		f.write(heredoc)
	
		try:
			for step in steps:
				f.write("<tr><td>" + str(step[0]) + "</td><td>" + str(step[1]) + "</td><td>" + str(step[2]) + "</td><td>" + str(step[3]) + "</td></tr>\n")
		except IndexError:
			pass

		heredoc = """</tbody>
</table>
</td>
"""
		f.write(heredoc)

def printTotalW1(f, steps, index):
	totalW1 = 0
	try:
		for step in steps:
			totalW1 += step[index]
	except IndexError:
		pass
	f.write("<td style=\"vertical-align:middle\">" + str(totalW1) + "</td>\n")

def readInitLog(afile):
	results = InitLog()

	#Name: f2
	reN = re.compile(r"Name: (.+)")
	#0) W2 pH=7.19 after adding 4.735214 ml W1
	pH0 = re.compile(r"(\d+)\) W2 pH\=(\d+\.\d+) after adding (\d+\.\d+) ml W1")
	#AUTOPH: step: 0 start: 5.965 end: 6.707 vol: 4.337
	pHn = re.compile(r"AUTOPH: step: (\d+) start: (\d+\.\d+) end: (\d+\.\d+) vol: (\d+\.\d+)")

	try:
		results.fileName = afile
		with open(afile, 'r') as f:
			results.missing = False
			for line in f:
				line = line.strip()
			
				#Name: f2
				m = reN.match(line)
				try:
					results.instName = m.group(1)
				except AttributeError:
					pass

				try:
					#Wed Feb 27 15:27:51 2013
					results.dates.append(datetime.datetime.strptime(line, "%a %b %d %H:%M:%S %Y"))
				except ValueError:
					pass
			
				#0) W2 pH=7.19 after adding 4.735214 ml W1
				m = pH0.match(line)
				try:
					stepN = int(m.group(1))
					pHval = float(m.group(2))
					W1add = float(m.group(3))
					results.midSteps.append([stepN, pHval, W1add])
				except AttributeError:
					pass

				#AUTOPH: step: 0 start: 5.965 end: 6.707 vol: 4.337
				m = pHn.match(line)
				try:
					stepN = int(m.group(1))
					pHbeg = float(m.group(2))
					pHend = float(m.group(3))
					W1add = float(m.group(4))
					results.endSteps.append([stepN, pHbeg, pHend, W1add])
				except AttributeError:
					pass

				if "Aborted" in line:
					results.aborted = True
					if "Aborted" not in results.issues:
						if (len(results.issues)):
							results.issues = results.issues + "<br/>Aborted"
						else:
							results.issues = "Aborted"

				if "OVERSHOT" in line:
					if "Overshot" not in results.issues:
						if (len(results.issues)):
							results.issues = results.issues + "<br/>Overshot"
						else:
							results.issues = "Overshot"
			
				if "UNDERSHOT" in line:
					if "Undershot" not in results.issues:
						if (len(results.issues)):
							results.issues = results.issues + "<br/>Undershot"
						else:
							results.issues = "Undershot"
			
				if "W2 Calibrate Passed" in line:
					results.outcome = "Passed"
			
	except IOError:
		pass
	
	return results

def writeOutputPreamble(f, instNameIn):
	heredoc = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>{instName} Auto pH Runs, newest to oldest:</title>
<link href="http://inspector.itw/static/css/bootstrap.css" rel="stylesheet"/>
<style type="text/css">
      body {{
        padding: 30px;
      }}
.title {{
  font-size: xx-large;
  float:left;
  padding: 35px;
}}
.phPass {{
  color: #33bb33;
  font-weight: bold;
  vertical-align:middle;
}}
.phAlert {{
  color: #cc4444;
  font-weight: bold;
  vertical-align:middle;
}}
.table-stripe2 tbody > tr:nth-child(odd) > td,
.table-stripe2 tbody > tr:nth-child(odd) > th {{
  background-color: #f9f9f9;
}}

</style>
</head>

<body>

<div class="title">
<p>{instName} Auto pH runs, newest to oldest:</p>
</div>

<div class="container">
<div class="row">
<div class="span12">
<table id="test-summary" class="table table-striped">
<thead>
<tr>
<th>Run #</th><th>Outcome</th><th>Issues?</th><th>Timing</th><th>Details for each Iteration</th><th>Total W1 Added (ml)</th>
</tr>
</thead>
<tbody>
"""
	f.write(heredoc.format(instName=instNameIn))

def writeOutputPostscript(f):
	heredoc = """
</tbody>
</table>
</div>
</div>
</div>
</body>
</html>
"""
	f.write(heredoc)

if __name__ == '__main__': 
	main()
