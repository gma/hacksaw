# $Id$
# (C) Cmed Ltd, 2004


import os
import shutil
import sys
import unittest

from pmock import *

import hacksaw.lib
import processlogs


class ProcessorTest(unittest.TestCase):

    SPOOL_DIR = './test-spool'
    filename = './test.conf'

    def append_to_file(self, line):
        file(self.filename, 'a').write(line)
        self.config = hacksaw.lib.GeneralConfig(self.filename)
        
    def setUp(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)
        self.append_to_file('[general]\nspool: %s\n' % self.SPOOL_DIR)

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)


class NoSpoolDirTest(ProcessorTest):

    SPOOL_DIR = '/no/such/directory'

    def test_no_spool_dir(self):
        """Check exception raised if spool directory not found"""
        self.assertRaises(IOError, processlogs.process_log_files, self.config)


class SingleProcessorTest(ProcessorTest):

    def setUp(self):
        ProcessorTest.setUp(self)
        self.append_to_file("processors: hacksaw.proc.test\n")

    def test_get_one_processor(self):
        """Check we can get a single processor"""
        try:
            module = Mock()
            config = Mock()
            module.expects(
                once()).Config(eq(self.filename)).will(return_value(config))
            module.expects(once()).Processor(eq(config))
            sys.modules['hacksaw.proc.test'] = module
            processors = processlogs.get_processors(self.config)
            self.assertEquals(len(processors), 1)
            module.verify()
        finally:
            del sys.modules['hacksaw.proc.test']


class MultipleProcessorTest(ProcessorTest):

    def setUp(self):
        ProcessorTest.setUp(self)
        self.append_to_file(
            "processors: hacksaw.proc.test1, hacksaw.proc.test2\n")
    
    def test_get_two_processors(self):
        """Check we can get multiple processors"""
        try:
            module = Mock()
            config = Mock()
            module.expects(
                once()).Config(eq(self.filename)).will(return_value(config))
            module.expects(once()).Processor(eq(config))
            module.expects(
                once()).Config(eq(self.filename)).will(return_value(config))
            module.expects(once()).Processor(eq(config))
            sys.modules['hacksaw.proc.test1'] = module
            sys.modules['hacksaw.proc.test2'] = module
            processors = processlogs.get_processors(self.config)
            self.assertEquals(len(processors), 2)
            module.verify()
        finally:
            del sys.modules['hacksaw.proc.test1']
            del sys.modules['hacksaw.proc.test2']


class MissingProcessorTest(ProcessorTest):

    def setUp(self):
        ProcessorTest.setUp(self)
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


class UseProcessorsTest(ProcessorTest):

    def mock_get_processors(self, config):
        self.processor = Mock()
        self.processor.expects(once()).handle_message(eq('Message 1'))
        return [self.processor]

    def make_log_file(self):
        if os.path.exists(UseProcessorsTest.SPOOL_DIR):
            shutil.rmtree(UseProcessorsTest.SPOOL_DIR)
        os.mkdir(UseProcessorsTest.SPOOL_DIR)
        log = file(os.path.join(UseProcessorsTest.SPOOL_DIR, 'test.log'), 'w')
        log.write('Message 1')
        log.close()
        
    def setUp(self):
        self.real_func = processlogs.get_processors
        processlogs.get_processors = self.mock_get_processors
        ProcessorTest.setUp(self)
        self.make_log_file()

    def tearDown(self):
        processlogs.get_processors = self.real_func
        ProcessorTest.tearDown(self)
        shutil.rmtree(UseProcessorsTest.SPOOL_DIR)

    def test_single_file(self):
        """Check the processors are run on each spooled log message"""
        processlogs.process_log_files(self.config)
        self.processor.verify()


if __name__ == '__main__':
    unittest.main()
