#!/usr/bin/env python
#
# $Id$
# (C) Cmed Ltd, 2004


import sys


HACKSAW_CONF_FILE = '/etc/hacksaw.conf'


def usage():
    print "Usage: run-processor.py <processor name>"


if __name__ == "__main__":
    try:
        processor_name = sys.argv[1]
    except IndexError:
        usage()
        sys.exit(1)
    try:
        __import__(processor_name)
    except ImportError, e:
        sys.stderr.write("Error: %s" % e)
        sys.exit(1)
    else:
        processor_module = sys.modules[processor_name]
    processor_module.main([HACKSAW_CONF_FILE])
