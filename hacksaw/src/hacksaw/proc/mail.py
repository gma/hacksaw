# $Id$
# (C) Cmed Ltd, 2004


import email.MIMEText
import errno
import fcntl
import os
import re
import sys
import time

import hacksaw.lib


class Processor(hacksaw.lib.Processor):

    LOCK_TIMEOUT = 5

    def __init__(self, config):
        hacksaw.lib.Processor.__init__(self, config)
        dirname = os.path.dirname(self.config.message_store)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    def acquire_lock(self):
        file_obj = file(self.config.message_store, "a")
        try:
            fcntl.lockf(file_obj.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError, e:
            if e.errno in (errno.EACCES, errno.EAGAIN):
                return None
            raise
        return file_obj
        
    def handle_message(self, message):
        file_obj = self.acquire_lock()
        start_time = time.time()
        while file_obj is None:
            if time.time() - start_time >= Processor.LOCK_TIMEOUT:
                raise IOError("Couldn't write to '%s' within %s seconds" %
                              (self.config.filename, Processor.LOCK_TIMEOUT))
            file_obj = self.acquire_lock()
        file_obj.write(message)
        file_obj.close()


class Config(hacksaw.lib.Config):

    MESSAGE_STORE = 'messagestore'
    SENDER = 'sender'
    RECIPIENTS = 'recipients'
    SUBJECT = 'subject'
    MAIL_COMMAND = 'mailcommand'
    MAX_MESSAGE_STORE = 'max_messagestore'

    def _get_message_store(self):
        return self._get_item(Config.MESSAGE_STORE)

    message_store = property(_get_message_store)

    def _get_sender(self):
        return self._get_item(Config.SENDER)

    sender = property(_get_sender)

    def _get_recipients(self):
        recipients = []
        for word in self._get_item(Config.RECIPIENTS).split(','):
            recipients.append(word.strip())
        return recipients

    recipients = property(_get_recipients)

    def _get_subject(self):
        return self._get_item(Config.SUBJECT)

    subject = property(_get_subject)

    def _get_mail_command(self):
        return self._get_item(Config.MAIL_COMMAND)

    mail_command = property(_get_mail_command)

    def _get_max_message_store(self):
        return int(self._get_item(Config.MAX_MESSAGE_STORE))

    max_message_store = property(_get_max_message_store)


class MessageSender(object):

    def __init__(self, config):
        self.config = config

    def addresses_are_valid(self):
        for recipient in self.config.recipients:
            pattern = re.compile('[\w.-]+@[\w.-]+$')
            if not bool(pattern.match(recipient.strip())):
                return False
        return True

    def _get_log_attachment(self):
	log_messages = file(self.config.message_store, "r").read()
	message = email.MIMEText.MIMEText(log_messages)
	message.add_header('Content-Disposition', 'attachment',
                           filename='logs.txt')
	return message
	 
    def _get_message(self):
	message = email.MIMEBase.MIMEBase('multipart', 'mixed')
	message.epilogue = "" # guarantees ends in new line
	message["From"] = self.config.sender
	message["To"] = ', '.join(self.config.recipients)
	message["Subject"] = self.config.subject
        message.attach(self._get_log_attachment())
	return message

    def send_message_too_large_error(self):
	message = email.MIMEBase.MIMEBase('text', 'plain')
	message.epilogue = "" # guarantees ends in new line
	message["From"] = self.config.sender
	message["To"] = ', '.join(self.config.recipients)
	message["Subject"] = "Hacksaw error: Message store is too large"
        message_str = message.as_string(unixfrom=0)
        fd = os.popen(self.config.mail_command, 'w')
        fd.write(message_str)
        rval = fd.close()
        if rval is None:
            pass
        else:
            sys.stderr.write('Error: sendmail returned %s\n' % rval)
        return rval

    def send_message(self):
        message = self._get_message().as_string(unixfrom=0)
        if len(message) > self.config.max_message_store * 1024:
            return self.send_message_too_large_error()
        fd = os.popen(self.config.mail_command, 'w')
        fd.write(message)
        rval = fd.close()
        if rval is None:
            os.remove(self.config.message_store)
        else:
            sys.stderr.write('Error: sendmail returned %s\n' % rval)
        return rval


class Usage(Exception):

    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    try:
        try:
            config_file = argv[0]
        except IndexError:
            raise Usage
        config = Config(config_file)
        sender = MessageSender(config)
        sender.send_message()
    except Usage, e:
        print >>sys.stderr, e.msg
        return 2
    except Exception, e:
        print >>sys.stderr, e
    return 0
