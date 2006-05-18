# $Id$
# (C) Cmed Ltd, 2004


import os
import shutil
import sys
import time
import unittest

from pmock import *

import hacksaw.lib_test
import hacksaw.proc.mail


class MailTest(hacksaw.lib_test.ConfigTest):

    config_cls = hacksaw.proc.mail.Config
    MESSAGE_STORE = "./path/message_store"

    def setUp(self):
        hacksaw.lib_test.ConfigTest.setUp(self)
        self.append_to_file("[hacksaw.proc.mail]")
        self.append_to_file("messagestore: %s" % MailTest.MESSAGE_STORE)
        self.read_config()

    def tearDown(self):
        hacksaw.lib_test.ConfigTest.tearDown(self)
        if os.path.exists(os.path.dirname(MailTest.MESSAGE_STORE)):
            shutil.rmtree(os.path.dirname(MailTest.MESSAGE_STORE))
    

class ProcessorTest(MailTest):
    
    def test_write_to_message_store(self):
        """Check that we write log messages to the correct file"""
        processor = hacksaw.proc.mail.Processor(self.config)
        processor.handle_message("Test message")
        message_store = file(self.config.message_store, "r")
        self.assert_(message_store.read(), "Test message\n")

    def test_can_lock(self):
        """Check we can lock the message store"""
        processor = hacksaw.proc.mail.Processor(self.config)
        file_obj = processor.acquire_lock()
        self.assertNotEqual(file_obj, None)
        code = """
import sys

import hacksaw.proc.mail

config = hacksaw.proc.mail.Config("%s")
processor = hacksaw.proc.mail.Processor(config)
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
       
        processor = hacksaw.proc.mail.Processor(self.config)
        processor.acquire_lock = acquire_func
        processor.handle_message("Test message")
        mock.verify()

    def test_lock_timeout(self):
        """Check the lock attempt times out"""
        mock_time = Mock()
        t0 = time.time()
        timeout = hacksaw.proc.mail.Processor.LOCK_TIMEOUT
        mock_time.expects(once()).time().will(return_value(t0 + timeout))
        mock_time.expects(once()).time().will(return_value(t0))
        real_time = hacksaw.proc.mail.time
        hacksaw.proc.mail.time = mock_time

        def acquire_func():
            return None

        try:
            processor = hacksaw.proc.mail.Processor(self.config)
            processor.acquire_lock = acquire_func
            self.assertRaises(IOError, processor.handle_message,
                              "Test message")
        finally:
            hacksaw.proc.mail.time = real_time
       

class ConfigTest(MailTest):

    def test_get_message_store(self):
        """Check we can get the path to the summary file"""
        path = "/path/to/message/store"
        self.append_to_file("messagestore: %s" % path)
        self.read_config()
        self.assertEqual(self.config.message_store, path)

    def test_get_sender(self):
        """Check we can get the sender address"""
        self.append_to_file("sender: wilber@cmedltd.com")
        self.read_config()
        self.assertEqual(self.config.sender, "wilber@cmedltd.com")

    def test_get_recipients(self):
        """Check we can get the recipient addresses"""
        recipients = "bob@foo.com, ged@localhost"
        self.append_to_file("recipients: %s" % recipients)
        self.read_config()
        self.assertEqual(self.config.recipients,
                         ["bob@foo.com", "ged@localhost"])

    def test_get_subject(self):
        """Check we can get the email subject"""
        self.append_to_file("subject: Hacksaw e-mail")
        self.read_config()
        self.assertEqual(self.config.subject, "Hacksaw e-mail")

    def test_get_mail_command(self):
        """Check we can get the command for sending mail"""
        sendmail = "/usr/lib/sendmail -t"
        self.append_to_file("mailcommand: %s" % sendmail)
        self.read_config()
        self.assertEqual(self.config.mail_command, sendmail)

    def test_get_maximum_message_store_size(self):
        """Check we can get the maximum message store size"""
        max_message_store = 1024
        self.append_to_file("max_messagestore: %s" % max_message_store)
        self.read_config()
        self.assertEqual(self.config.max_message_store, max_message_store)


class MessageSenderTest(MailTest):
    
    def setUp(self):
	MailTest.setUp(self)
	dirname = os.path.dirname(MailTest.MESSAGE_STORE)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
	file(MailTest.MESSAGE_STORE, "a").write("Error: Example Message\n")

    def test_address_validity_when_valid(self):
        """Check we allow valid addresses"""
        self.append_to_file("recipients: bob@foo.com, ged@localhost")
        self.read_config()
        sender = hacksaw.proc.mail.MessageSender(self.config)
        self.assert_(sender.addresses_are_valid())

    def test_address_validity_when_invalid(self):
        """Check we don't send messages to invalid addresses"""
        self.append_to_file("recipients: bob@foo.com, ged at localhost")
        self.read_config()
        sender = hacksaw.proc.mail.MessageSender(self.config)
        self.failIf(sender.addresses_are_valid())

    def _setup_mock_pipe(self, file_obj):
        self.append_to_file('sender: wilber@cmedltd.com')
        self.append_to_file('recipients: gteale@cmedltd.com')
        self.append_to_file('subject: Hacksaw e-mail')
        self.append_to_file('mailcommand: /usr/lib/sendmail -t')
        self.read_config()
        mock_os = Mock()
        mock_os.expects(once()).popen(
            eq('/usr/lib/sendmail -t'), eq('w')).will(return_value(file_obj))
        
        self.real_os = hacksaw.proc.mail.os
        hacksaw.proc.mail.os = mock_os
	return mock_os

    def _remove_mock_pipe(self):
	hacksaw.proc.mail.os = self.real_os

    def test_use_correct_mail_command(self):
        """Check that the correct mail command is used to send mail"""
        self.append_to_file("max_messagestore: 1")
        self.read_config()
        file_obj = Mock()
        file_obj.expects(once()).method("close")
        file_obj.expects(once()).method("write")
	mock_os = self._setup_mock_pipe(file_obj)
        mock_os.expects(once()).remove(eq(MailTest.MESSAGE_STORE))
        try:
            sender = hacksaw.proc.mail.MessageSender(self.config)
            sender.send_message()
	    file_obj.verify()
            mock_os.verify()
        finally:
	    self._remove_mock_pipe()
        
    def test_log_attachment(self):
        """Check that the log messages are attached to the mail"""
        self.append_to_file("max_messagestore: 1")
        self.read_config()
        file_obj = Mock()
        file_obj.expects(once()).close()
        file_obj.expects(once()).write(
	    string_contains("Error: Example Message"))
	mock_os = self._setup_mock_pipe(file_obj)
        mock_os.expects(once()).remove(eq(MailTest.MESSAGE_STORE))
        try:
            sender = hacksaw.proc.mail.MessageSender(self.config)
            sender.send_message()
	    file_obj.verify()
            mock_os.verify()
        finally:
	    self._remove_mock_pipe()

    def test_deletion(self):
        """Check message store deleted if mail sent"""
        self.append_to_file("max_messagestore: 1")
        self.read_config()
        file_obj = Mock()
        file_obj.expects(once()).method("close").will(return_value(None))
        file_obj.expects(once()).write(
	    string_contains("Error: Example Message"))
	mock_os = self._setup_mock_pipe(file_obj)
        mock_os.expects(once()).remove(eq(MailTest.MESSAGE_STORE))
        try:
            sender = hacksaw.proc.mail.MessageSender(self.config)
            sender.send_message()
	    file_obj.verify()
            mock_os.verify()
        finally:
	    self._remove_mock_pipe()

    def test_unsuccessful_send(self):
        """Check message store not deleted if mail not sent"""
        self.append_to_file("max_messagestore: 1")
        self.read_config()
        file_obj = Mock()
        file_obj.expects(once()).method("close").will(return_value(1))
        file_obj.expects(once()).write(
	    string_contains("Error: Example Message"))
	mock_os = self._setup_mock_pipe(file_obj)
        sys.stderr = Mock()
        sys.stderr.expects(once()).write(string_contains("Error:"))
        try:
            sender = hacksaw.proc.mail.MessageSender(self.config)
            sender.send_message()
	    file_obj.verify()
            mock_os.verify()
            self.assert_(os.path.exists(MailTest.MESSAGE_STORE))
        finally:
	    self._remove_mock_pipe()
            sys.stderr = sys.__stderr__


class SendErrorTest(MessageSenderTest):
    
    def _setup_mock_pipe(self, file_obj):
        self.append_to_file('sender: wilber@cmedltd.com')
        self.append_to_file('recipients: gteale@cmedltd.com')
        self.append_to_file('subject: Hacksaw error: Message store too large')
        self.append_to_file('mailcommand: /usr/lib/sendmail -t')
        self.read_config()
        mock_os = Mock()
        mock_os.expects(once()).popen(
            eq('/usr/lib/sendmail -t'), eq('w')).will(return_value(file_obj))
        
        self.real_os = hacksaw.proc.mail.os
        hacksaw.proc.mail.os = mock_os
	return mock_os

    def _remove_mock_pipe(self):
	hacksaw.proc.mail.os = self.real_os

    def test_message_store_too_large(self):
        """Check error message is sent if message store too large"""
        self.append_to_file("max_messagestore: 0")
        self.read_config()
        file_obj = Mock()
        file_obj.expects(once()).close()
        file_obj.expects(once()).write(
	    string_contains("Subject: Hacksaw error:"))
	mock_os = self._setup_mock_pipe(file_obj)
        try:
            sender = hacksaw.proc.mail.MessageSender(self.config)
            sender.send_message()
	    file_obj.verify()
            mock_os.verify()
        finally:
	    self._remove_mock_pipe()


if __name__ == '__main__':
    unittest.main()
