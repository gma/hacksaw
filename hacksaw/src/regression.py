#!/usr/bin/env python
#
# regression.py - alternative unit testing script, useful during coding.
#
# Runs all tests that it finds beneath the current directory.
#
# Usage: regression.py [-q|-v]
#
# Options:
#     -q  --  quiet (prints no output while running tests, only summary)
#     -v  --  verbose (prints name of each test)
#
# $Id$


import getopt
import os
import sys
import unittest


class DevNull:

    def write(self, message):
        pass

    def flush(self):
        pass


def get_verbosity():
    verbosity = 1  # default
    opts, args = getopt.getopt(sys.argv[1:], "qv")
    for o, v in opts:
        if o == "-q":
            verbosity = 0
        if o == "-v":
            verbosity = 2
    return verbosity


def load_tests(arg, dirname, names):
    global suite
    names = [name for name in names if not name.startswith('.')]
    if dirname.endswith(os.path.join("tests", "unit")):
        files = os.listdir(dirname)
        tests = filter(lambda f: f.endswith(".py"), files)
    else:
        tests = filter(lambda f: f.endswith("_test.py"), names)
    cur_dir = os.getcwd()
    os.chdir(os.path.abspath(dirname))
    for test in tests:
        modname, ext = os.path.splitext(test)
        modsuite = unittest.defaultTestLoader.loadTestsFromName(modname)
        suite.addTest(modsuite)
    os.chdir(cur_dir)


if __name__ == "__main__":
    #sys.stdout = DevNull()
    sys.path.append(".")
    suite = unittest.TestSuite()
    os.path.walk(".", load_tests, None)
    runner = unittest.TextTestRunner(verbosity=get_verbosity())
    runner.run(suite)
