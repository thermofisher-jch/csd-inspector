"""This folder contains a folder called tests.  Every folder within tests
contains a separate diagnostic with a 'main' script.  The main script is passed
two command line arguments, the full path to the folder containing the
decompressed support archive and the full path to the folder in which they
should place their results.  The current working directory will be the
directory containing the diagnostic, not the directory containing it's results.
"""

__author__ = 'bakennedy'

import os
import os.path


class Test(object):

    def __init__(self, directory, main):
        self.directory = os.path.abspath(directory)
        self.main = os.join(self.directory, main)
        readme = os.join(directory, "README")
        if os.path.exists(readme):
            self.readme = open(readme, 'rt').read()
        else:
            self.readme = None
        


def get_tests(test_directory):
    tests = []
    for path in os.listdir(test_directory):
        if os.path.isdir(path):
            for filename in os.listdir(path):
                if filename.startswith("main"):
                    tests.append(Test(path, filename))
    return tests

