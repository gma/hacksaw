#!/usr/bin/env python
#
# $Id$
# (C) Cmed Ltd, 2004


import ConfigParser
import getopt
import os
import sys

import hacksaw


def get_processors(config):
    cls = getattr(hacksaw, config.processors + 'Processor')
    return [cls()]


def process_log_files(config):
    if not os.path.exists(config.spool_directory):
        raise IOError, 'file not found: %s' % config.spool_directory
    processors = get_processors(config)
    for log_file in os.listdir(config.spool_directory):
        for line in file(os.path.join(config.spool_directory, log_file)):
            for processor in processors:
                processor.handle_message(line)
            

class Usage(RuntimeError):

    pass


def main(argv=None):
    config_file = os.path.join('..', 'etc', 'hacksaw.conf')
    if argv is None:
        argv = sys.argv[1:]
    try:
        try:
            opts, args = getopt.getopt(argv, "c")
        except getopt.error, msg:
            raise Usage(msg)
        for opt, arg in opts:
            if opt == '-c':
                config_file = arg
        config = hacksaw.Config(config_path)
        process_log_files(config)
    except Usage, e:
        print >>sys.stderr, e.msg
        print >>sys.stderr, "processlogs.py -c"
        return 2
    except Exception, e:
        print >>sys.stderr, e



if __name__ == '__main__':
    sys.exit(main())

