# $Id$
# (C) Cmed Ltd, 2004


import os
import shutil
import sys
import time
import unittest

from pmock import *

import hacksaw.lib_test
import hacksaw.proc.logfile


class LogfileTest(hacksaw.lib_test.ConfigTest):

    config_cls = hacksaw.proc.logfile.Config
    LOG_FILE = "./path/log_file"

    def setUp(self):
        hacksaw.lib_test.ConfigTest.setUp(self)
        self.append_to_file("[hacksaw.proc.logfile]")
        self.append_to_file("logfile: %s" % LogfileTest.LOG_FILE)

    def tearDown(self):
        hacksaw.lib_test.ConfigTest.tearDown(self)
        if os.path.exists(os.path.dirname(LogfileTest.LOG_FILE)):
            shutil.rmtree(os.path.dirname(LogfileTest.LOG_FILE))
    

class ProcessorTest(LogfileTest):
    
    def test_write_to_log_file(self):
        """Check that we write log messages to the correct file"""
        processor = hacksaw.proc.logfile.Processor(self.config)
        processor.handle_message("Test message")
        log_file = file(self.config.log_file, "r")
        self.assert_(log_file.read(), "Test message\n")

    def test_can_lock(self):
        """Check we can lock the message store"""
        processor = hacksaw.proc.logfile.Processor(self.config)
        file_obj = processor.acquire_lock()
        self.assertNotEqual(file_obj, None)
        code = """
import sys

import hacksaw.proc.logfile

config = hacksaw.proc.logfile.Config("%s")
processor = hacksaw.proc.logfile.Processor(config)
if processor.acquire_lock() is None:
    sys.exit(0)
else:
    sys.exit(1)
    
""" % self.filename
        self.assertEqual(os.system("""python -c '%s'""" % code) >> 8, 0)

    def test_use_lock(self):
        """Check we lock the message store when appending a message"""
        file_obj = Mock()
        file_obj.expects(once()).write(eq("Test message"))
        file_obj.expects(once()).close()
       
        mock = Mock()
        mock.expects(once()).register().will(return_value(file_obj))
        mock.expects(once()).register().will(return_value(None))
              
        def acquire_func():
            rval = mock.register()
            return rval
       
        processor = hacksaw.proc.logfile.Processor(self.config)
        processor.acquire_lock = acquire_func
        processor.handle_message("Test message")
        mock.verify()

    def test_lock_timeout(self):
        """Check the lock attempt times out"""
        mock_time = Mock()
        t0 = time.time()
        timeout = hacksaw.proc.logfile.Processor.LOCK_TIMEOUT
        mock_time.expects(once()).time().will(return_value(t0 + timeout))
        mock_time.expects(once()).time().will(return_value(t0))
        real_time = hacksaw.proc.logfile.time
        hacksaw.proc.logfile.time = mock_time

        def acquire_func():
            return None

        try:
            processor = hacksaw.proc.logfile.Processor(self.config)
            processor.acquire_lock = acquire_func
            self.assertRaises(IOError, processor.handle_message,
                              "Test message")
        finally:
            hacksaw.proc.logfile.time = real_time
       

class ConfigTest(LogfileTest):

    def test_get_log_file(self):
        """Check we can get the path to the log file"""
        path = "/path/to/log/file"
        self.append_to_file("logfile: %s" % path)
        self.assertEqual(self.config.log_file, path)


if __name__ == '__main__':
    unittest.main()
