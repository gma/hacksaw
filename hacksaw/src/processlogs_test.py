# $Id$
# (C) Cmed Ltd, 2004


import os
import shutil
import sys
import unittest

from pmock import *

import hacksaw.lib
import processlogs


class ProcessTest(unittest.TestCase):

    SPOOL_DIR = './test-spool'
    CONF_FILE = './test.conf'


    def append_to_file(self, line):
        file(self.CONF_FILE, 'a').write(line)
        self.config = hacksaw.lib.Config(self.CONF_FILE)
        
    def setUp(self):
        assert not os.path.exists(self.CONF_FILE)
        self.append_to_file('[general]\nspool: %s\n' % self.SPOOL_DIR)

    def tearDown(self):
        if os.path.exists(self.CONF_FILE):
            os.remove(self.CONF_FILE)


class NoSpoolDirTest(ProcessTest):

    SPOOL_DIR = '/no/such/directory'

    def test_no_spool_dir(self):
        """Check exception raised if spool directory not found"""
        self.assertRaises(IOError, processlogs.process_log_files, self.config)


class SingleProcessorTest(ProcessTest):

    def setUp(self):
        ProcessTest.setUp(self)
        self.append_to_file("processors: hacksaw.proc.email\n")

    def test_get_one_processor(self):
        """Check we can get a single processor"""
        processors = processlogs.get_processors(self.config)
        self.assertEquals(len(processors), 1)
        self.assert_(isinstance(processors[0], hacksaw.proc.email.Processor))


class MultipleProcessorTest(ProcessTest):

    def setUp(self):
        ProcessTest.setUp(self)
        self.append_to_file(
            "processors: hacksaw.proc.email, hacksaw.proc.syslog\n")
    
    def test_get_two_processors(self):
        """Check we can get multiple processors"""
        processors = processlogs.get_processors(self.config)
        self.assertEquals(len(processors), 2)
        self.assert_(isinstance(processors[0], hacksaw.proc.email.Processor))
        self.assert_(isinstance(processors[1], hacksaw.proc.syslog.Processor))


class MissingProcessorTest(ProcessTest):

    def setUp(self):
        ProcessTest.setUp(self)
        self.append_to_file(
            "processors: missing.processor\n")

    def test_get_missing_processor(self):
        """Check that attempting to get a missing processor produces error"""
        try:
            sys.stderr = Mock()
            sys.stderr.expects(once()).write(string_contains('Error:'))
            processlogs.get_processors(self.config)
            sys.stderr.verify()
        finally:
            sys.stderr = sys.__stderr__


class FilesTest(ProcessTest):

    def mock_get_processors(self, config):
        self.processor = Mock()
        self.processor.expects(once()).handle_message(eq('Message 1'))
        return [self.processor]

    def make_log_file(self):
        if os.path.exists(FilesTest.SPOOL_DIR):
            shutil.rmtree(FilesTest.SPOOL_DIR)
        os.mkdir(FilesTest.SPOOL_DIR)
        log = file(os.path.join(FilesTest.SPOOL_DIR, 'test.log'), 'w')
        log.write('Message 1')
        log.close()
        
    def setUp(self):
        self.real_func = processlogs.get_processors
        processlogs.get_processors = self.mock_get_processors
        ProcessTest.setUp(self)
        self.make_log_file()

    def tearDown(self):
        processlogs.get_processors = self.real_func
        ProcessTest.tearDown(self)
        shutil.rmtree(FilesTest.SPOOL_DIR)

    def test_single_file(self):
        """Check the processors are run on each spooled log message"""
        processlogs.process_log_files(self.config)
        self.processor.verify()


if __name__ == '__main__':
    unittest.main()
    
