# $Id$
# (C) Cmed Ltd, 2004


import os
import shutil
import time
import unittest

from pmock import *

import hacksaw.lib_test
import hacksaw.proc.email


class EMailTest(hacksaw.lib_test.ConfigTest):

    config_cls = hacksaw.proc.email.Config
    MESSAGE_STORE = "./path/message_store"

    def setUp(self):
        hacksaw.lib_test.ConfigTest.setUp(self)
        self.append_to_file("[hacksaw.proc.email]")
        self.append_to_file("messagestore: %s" % EMailTest.MESSAGE_STORE)

    def tearDown(self):
        hacksaw.lib_test.ConfigTest.tearDown(self)
        if os.path.exists(os.path.dirname(EMailTest.MESSAGE_STORE)):
            shutil.rmtree(os.path.dirname(EMailTest.MESSAGE_STORE))
    

class ProcessorTest(EMailTest):
    
    def test_write_to_message_store(self):
        """Check that we write log messages to the correct file"""
        processor = hacksaw.proc.email.Processor(self.config)
        processor.handle_message("Test message")
        message_store = file(self.config.message_store, "r")
        self.assert_(message_store.read(), "Test message\n")

    def test_can_lock(self):
        """Check we can lock the message store"""
        processor = hacksaw.proc.email.Processor(self.config)
        file_obj = processor.acquire_lock()
        self.assertNotEqual(file_obj, None)
        code = """
import fcntl
import sys

import hacksaw.proc.email

config = hacksaw.proc.email.Config("%s")
processor = hacksaw.proc.email.Processor(config)
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
       
        processor = hacksaw.proc.email.Processor(self.config)
        processor.acquire_lock = acquire_func
        processor.handle_message("Test message")
        mock.verify()

    def test_lock_timeout(self):
        """Check the lock attempt times out"""
        mock_time = Mock()
        t0 = time.time()
        timeout = hacksaw.proc.email.Processor.LOCK_TIMEOUT
        mock_time.expects(once()).time().will(return_value(t0 + timeout))
        mock_time.expects(once()).time().will(return_value(t0))
        real_time = hacksaw.proc.email.time
        hacksaw.proc.email.time = mock_time

        def acquire_func():
            return None

        try:
            processor = hacksaw.proc.email.Processor(self.config)
            processor.acquire_lock = acquire_func
            self.assertRaises(IOError, processor.handle_message, "Test message")
        finally:
            hacksaw.proc.email.time = real_time
       

class ConfigTest(EMailTest):

    def test_get_message_store(self):
        """Check we can get the path to the summary file"""
        path = "/path/to/message/store"
        self.append_to_file("messagestore: %s" % path)
        self.assertEqual(self.config.message_store, path)

    def test_get_recipients(self):
        """Check we can get the path to the summary file"""
        recipients = "bob@foo.com, ged@localhost"
        self.append_to_file("recipients: %s" % recipients)
        self.assertEqual(self.config.recipients,
                         ["bob@foo.com", "ged@localhost"])

    def test_get_mail_command(self):
        """Check we can get the command for sending mail"""
        sendmail = "/usr/lib/sendmail -t"
        self.append_to_file("mailcommand: %s" % sendmail)
        self.assertEqual(self.config.mail_command, sendmail)


class MessageSenderTest(EMailTest):

    def test_address_validity_when_valid(self):
        """Check we allow valid addresses"""
        self.append_to_file("recipients: bob@foo.com, ged@localhost")
        sender = hacksaw.proc.email.MessageSender(self.config)
        self.assert_(sender.addresses_are_valid())

    def test_address_validity_when_invalid(self):
        """Check we don't send messages to invalid addresses"""
        self.append_to_file("recipients: bob@foo.com, ged at localhost")
        sender = hacksaw.proc.email.MessageSender(self.config)
        self.failIf(sender.addresses_are_valid())

    def test_use_correct_mail_command(self):
        """Check that the correct mail command is used to send mail"""
        self.append_to_file('mailcommand: /usr/lib/sendmail -t')
        file_obj = Mock()
        file_obj.expects(once()).method("close")
        file_obj.expects(once()).method("write")

        mock_os = Mock()
        mock_os.expects(once()).popen(eq('/usr/lib/sendmail -t'), eq('w')).will(
            return_value(file_obj))
        
        real_os = hacksaw.proc.email.os
        hacksaw.proc.email.os = mock_os

        try:
            sender = hacksaw.proc.email.MessageSender(self.config)
            sender.send_message()

            mock_os.verify()
        finally:
            hacksaw.proc.email.os = real_os
        
        
            

if __name__ == '__main__':
    unittest.main()
    
