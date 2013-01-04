#!/usr/bin/env python
"""This test always results in success, but it's a fancy example script too."""

import time
import sys
import os
import os.path
from string import Template

# This is the folder from which you can read all of the archive's contents
archive_path = sys.argv[1]
# This is the directory to which any files you write for any reason should be written.
output_path = sys.argv[2]
# You really only need to write this if people need to read it in order to 
# understand the result of your test on the current archive.
results_path = os.path.join(output_path, "results.html")

# Python has nice string templating available, which can be used for HTML.
# t = Template("$this") can be "that" by t.substitute({"this":"that"})
simple_html_template = Template("""
<html><body>
    <h1>$bold_summary</h1>
    <ul>
        <li>$foo</li>
        <li>$bar</li>
    </ul>
    <ol>$relative</ol>
    <ol>$full</ol>
</body></html>""")
# You could also have done this:
# simple_template = Template(open("simple_template.html").read())

# Accumulating your results in a dictionary will make rendering them in a
# template as easy as saying simple_template.substitute(that_dictionary)
results = dict(full="", relative="")
results["bold_summary"] = "This templating is fancy!"
results["foo"] = "It's simple,"
results["bar"] = "yet scalable."

# Here is how you get a list of the files in the archive
archive_files = os.listdir(archive_path)
# And here is how you get their archive relative and absolute paths.
for file_name in archive_files:
    results["relative"] += "<li>%s</li>" % file_name
    results["full"] += "<li>%s</li>" % os.path.join(archive_path, file_name)
    
# Stash all of your result variables in that HTML template we made and write it.
out = open(results_path, 'w')
out.write(simple_html_template.substitute(results))

# Sleep for dramatic effect, don't seriously do this in a real test.
time.sleep(5)

# Preferably wait until you're done to output your status
print("OK")
# This is the "Priority" it is used only to define the sort order of our
# Various tests in the final report.  There is some external correlation between
# Status and Priority that will be defined as this humble test framework grows
# in complexity and responsibility, I'm sure.
print(10)
# When at all possible, distil your results in to one or two plain text sentences
# and just print them here instead of writing a results.html file.
print("This test always results in success.")
