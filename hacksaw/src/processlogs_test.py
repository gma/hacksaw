# $Id$
# (C) Cmed Ltd, 2004


import os
import shutil
import unittest

from pmock import *

import hacksaw
import processlogs


class ProcessTest(unittest.TestCase):

    SPOOL_DIR = './test-spool'
    CONF_FILE = './test.conf'


    def append_to_file(self, line):
        file(self.CONF_FILE, 'a').write(line)
        self.config = hacksaw.Config(self.CONF_FILE)
        
    def setUp(self):
        self.append_to_file('[general]\nspool: %s\n' % self.SPOOL_DIR)

    def tearDown(self):
        if os.path.exists(self.CONF_FILE):
            os.remove(self.CONF_FILE)


class NoSpoolDirTest(ProcessTest):

    SPOOL_DIR = '/no/such/directory'

    def test_no_spool_dir(self):
        self.assertRaises(IOError, processlogs.process_log_files, self.config)


class GetProcessorsTest(ProcessTest):

    def setUp(self):
        ProcessTest.setUp(self)
        self.append_to_file("processors: EMail\n")

    def test_get_processors(self):
        processors = processlogs.get_processors(self.config)
        self.assertEquals(len(processors), 1)
        self.assert_(isinstance(processors[0], hacksaw.EMailProcessor))


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
        processlogs.process_log_files(self.config)
        self.processor.verify()
    

if __name__ == '__main__':
    unittest.main()
    
