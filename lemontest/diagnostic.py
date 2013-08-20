"""This folder contains a folder called tests.  Every folder within tests
contains a separate diagnostic with a 'main' script.  The main script is passed
two command line arguments, the full path to the folder containing the
decompressed support archive and the full path to the folder in which they
should place their results.  The current working directory will be the
directory containing the diagnostic, not the directory containing it's results.
"""

__author__ = 'Brian Kennedy'

import transaction
import subprocess
import os
import os.path
from glob import glob
from celery.task import task
from celery.utils.log import get_task_logger

from lemontest.models import DBSession
from lemontest.models import Diagnostic

logger = get_task_logger(__name__)

class Tester(object):

    def __init__(self, name, directory, main):
        self.name = name
        self.directory = directory
        self.main = os.path.join(self.directory, main)
        readmes = glob(os.path.join(directory, "README*"))
        if readmes:
            self.readme = readmes[0]
        else:
            self.readme = None

    def diagnostic_record(self):
        return Diagnostic(self.name)

@task
def echo(message):
    print("Printing " + message)
    logger.warning(message)

@task
def run_tester(test, diagnostic_id, archive_path):
    """Spawn a subshell in which the test's main script is run, with the
    archive's folder and the script's output folder as command line args.
    """
    logger.info("Running test %s/%d on %s" % (test.name, diagnostic_id, archive_path))
    # Now that we're finally running the task, set the status appropriately.
    diagnostic = DBSession.query(Diagnostic).get(diagnostic_id)
    output_path = diagnostic.get_output_path()
    diagnostic.status = u"Running"
    transaction.commit()

    os.mkdir(output_path)
    cmd = [test.main, archive_path, output_path]
    # Spawn the test subprocess and wait for it to complete.
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=test.directory)
    result = proc.wait()
    stdout, stderr = proc.communicate()
    open(os.path.join(output_path, "standard_output.log"), 'w').write(stdout)
    if stderr:
        open(os.path.join(output_path, "standard_error.log"), 'w').write(stderr)

    diagnostic = DBSession.query(Diagnostic).get(diagnostic_id)
    if result is 0:
        output = stdout.splitlines()
        status = output[0]
        priority = int(output[1])
        details = "\n".join(output[2:]).rstrip()
        html = os.path.join(output_path, "results.html")
        if os.path.exists(html):
            diagnostic.html = html
        logger.info("Test %s/%d completed with status %s" % (test.name, diagnostic_id, status))
    else:
        status = "TEST BROKEN"
        priority = 15
        details = "<div>Test %s ended with an error instead of running normally.\n<br />It output:</div><pre>%s</pre>" % \
                  (test.name, stdout)
        logger.warning("Test %s/%d ended with an error." % (test.name, diagnostic_id))
    # Update the record with the results.
    diagnostic.status = unicode(status)
    diagnostic.priority = priority
    diagnostic.details = unicode(details)
    transaction.commit()


def main_file(test_path):
    if os.path.isdir(test_path):
        for filename in os.listdir(test_path):
            if filename.startswith("main"):
                return filename
    return None


def get_testers(test_manifest, test_directory):
    test_list = dict()
    for archive_type, tests in test_manifest.items():
        test_list[archive_type] = dict()
        for test in tests:
            test_path = os.path.join(test_directory, test)
            filename = main_file(test_path)
            if filename is not None:
                tester = Tester(test, test_path, filename)
                test_list[archive_type][test] = tester
    return test_list


