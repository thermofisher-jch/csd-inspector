"""This folder contains a folder called tests.  Every folder within tests
contains a separate diagnostic with a 'main' script.  The main script is passed
two command line arguments, the full path to the folder containing the
decompressed support archive and the full path to the folder in which they
should place their results.  The current working directory will be the
directory containing the diagnostic, not the directory containing it's results.
"""

__author__ = 'bakennedy'

import transaction
import subprocess
import os
import os.path
from celery.task import task

from sqlalchemy import engine_from_config

from gnostic.models import DBSession
from gnostic.models import Diagnostic
from gnostic.models import initialize_sql


class Tester(object):

    def __init__(self, name, directory, main):
        self.name = name
        self.directory = directory
        self.main = os.path.join(self.directory, main)
        readme = os.path.join(directory, "README")
        if os.path.exists(readme):
            self.readme = open(readme, 'rt').read()
        else:
            self.readme = None

    def diagnostic_record(self):
        return Diagnostic(self.name)

@task
def run_tester(test, settings, diagnostic_id, archive_path):
    """Spawn a subshell in which the test's main script is run, with the
    archive's folder and the script's output folder as command line args.
    """
    logger = run_tester.get_logger()
    logger.info("Running test %s/%d on %s" % (test.name, diagnostic_id, archive_path))
    engine = engine_from_config(settings)
    initialize_sql(engine)
    # Now that we're finally running the task, set the status appropriately.
    session = DBSession()
    diagnostic = session.query(Diagnostic).get(diagnostic_id)
    diagnostic.status = u"Running"
    transaction.commit()
    # Open a DB session and fetch the diagnostic object to be updated.
    session = DBSession()
    diagnostic = session.query(Diagnostic).get(diagnostic_id)
    output_path = diagnostic.get_output_path()
    os.mkdir(output_path)
    cmd = [test.main, archive_path, output_path]
    # Spawn the test subprocess and wait for it to complete.
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=test.directory)
    result = proc.wait()
    stdout, stderr = proc.communicate()
    open(os.path.join(output_path, "standard_output.log"), 'w').write(stdout)
    if stderr:
        open(os.path.join(output_path, "standard_error.log"), 'w').write(stderr)
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
        priority = 100
        details = "Test %s ended with an error instead of running normally.\n<br />It output:\n<br /><pre>%s</pre>" % \
                  (test.name, stdout)
        logger.warning("Test %s/%d ended with an error." % (test.name, diagnostic_id))
    # Update the record with the results.
    diagnostic.status = unicode(status)
    diagnostic.priority = priority
    diagnostic.details = unicode(details)
    transaction.commit()


def get_testers(test_directory):
    tests = dict()
    for path in os.listdir(test_directory):
        test_path = os.path.join(test_directory, path)
        if os.path.isdir(test_path):
            for filename in os.listdir(test_path):
                if filename.startswith("main"):
                    tests[path] = Tester(path, test_path, filename)
    return tests

