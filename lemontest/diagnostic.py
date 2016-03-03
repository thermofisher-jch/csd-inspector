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
import time
import sys
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
def run_tester(test, diagnostic_id, archive_path):
    """Spawn a subshell in which the test's main script is run, with the
    archive's folder and the script's output folder as command line args.
    """
    timeout = 120
    logger.info("Running test %s/%d on %s" % (test.name, diagnostic_id, archive_path))
    # Now that we're finally running the task, set the status appropriately.
    diagnostic = DBSession.query(Diagnostic).get(diagnostic_id)
    output_path = diagnostic.get_output_path()
    diagnostic.status = u"Running"
    transaction.commit()
    try:
        os.mkdir(output_path)
        cmd = [test.main, archive_path, output_path]
        # Spawn the test subprocess and wait for it to complete.
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=test.directory)
        result = proc.poll()
        start_time = time.time()
        while result is None and time.time() - start_time < timeout:
            time.sleep(1)
            result = proc.poll()
    except Exception as err:
        logger.exception("Upload id={} test {} failed with an exception: {}".format(diagnostic.archive_id, diagnostic.name, err))
        diagnostic = DBSession.query(Diagnostic).get(diagnostic_id)
        diagnostic.status = u'System Failure'
        diagnostic.priority = 15
        diagnostic.details = u'There was an error in Ion Inspector, and this test could not run.'
        transaction.commit()
        return
    if result is not None:
        stdout, stderr = proc.communicate()
        open(os.path.join(output_path, "standard_output.log"), 'wb').write(stdout)
        if stderr:
            open(os.path.join(output_path, "standard_error.log"), 'wb').write(stderr)

    diagnostic = DBSession.query(Diagnostic).get(diagnostic_id)
    was_exception = ""
    if result is 0:
        output = stdout.decode("utf-8").splitlines()
        try:
            status = output[0]
            priority = int(output[1])
        except ValueError:
            was_exception = u"Line 1 of output was not an integer<br/>"
        except IndexError:
            was_exception = u"Too few lines of output<br/>"
        else:
            details = u"\n".join(output[2:]).rstrip()
            html = os.path.join(output_path, "results.html")
            if os.path.exists(html):
                diagnostic.html = unicode(html)
            logger.info("Test %s/%d completed with status %s" % (test.name, diagnostic_id, status))

    if result is not 0 or was_exception:
        if not was_exception:
            was_exception = u"Non-zero exit status"
        logger.error(u"Test Broken %s: %s" % (test.name, was_exception))
        status = u"TEST BROKEN"
        priority = 15
        if result is None:
            details = u"Test %s ran for longer than %d seconds without completing." % (test.name, timeout)
        else:
            details = u"<div>Test %s ended with an error instead of running normally.\n" % test.name
            if stdout:
                details += u"<br/>It output:<pre>%s</pre>" % stdout
                details += u"<br/>With error output:<pre>%s</pre>" % stderr
            else:
                details += u"It output nothing."
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


