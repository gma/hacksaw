# $Id$
# (C) Cmed Ltd, 2005


import re
import syslog

import netsyslog

import hacksaw.lib


class LogMessage(object):

    # This class was blatantly stolen from the Band Saw source.
    # See http://bandsaw.sourceforge.net/.

    regex = r"([^\s]+\s+[^\s]+\s+[^\s]+)\s+([^\s]+)\s+([^\s]+):\s(.*)"
    pattern = re.compile(regex)
    
    def __init__(self, line):
        self.match = LogMessage.pattern.match(line)

    def _get_message_part(self, index):
        try:
            return self.match.groups()[index]
        except AttributeError:
            return ""

    def _get_date(self):
        return self._get_message_part(0)

    date = property(_get_date)
    
    def _get_hostname(self):
        return self._get_message_part(1)

    hostname = property(_get_hostname)

    def _get_process(self):
        return self._get_message_part(2)

    process = property(_get_process)

    def _get_text(self):
        return self._get_message_part(3)

    text = property(_get_text)


class Processor(hacksaw.lib.Processor):

    def split_process_info(self, text):
        if "[" in text:
            name, pid = text.split("[")
            pid = int(pid[:-1])
        else:
            name = text
            pid = None
        return name, pid

    def create_packet(self, message):
        log = LogMessage(message)
        pri = netsyslog.PriPart(self.config.facility, self.config.priority)
        header = netsyslog.HeaderPart(log.date, log.hostname)
        process_name, pid = self.split_process_info(log.process)
        msg = netsyslog.MsgPart(process_name, log.text, pid)
        return netsyslog.Packet(pri, header, msg)

    def handle_message(self, message):
        packet = self.create_packet(message)
        logger = netsyslog.Logger()
        for host in self.config.hosts:
            logger.add_host(host)
            logger.send_packet(packet)


class Config(hacksaw.lib.Config):

    FACILITY = "facility"
    HOSTS = "hosts"
    PRIORITY = "priority"

    def _get_facility(self):
        name = self._get_item(Config.FACILITY)
        constant = "LOG_" + name.upper()
        return getattr(syslog, constant)

    facility = property(_get_facility)

    def _get_priority(self):
        name = self._get_item(Config.PRIORITY)
        if name == "warn":
            name = "warning"
        elif name == "error":
            name = "err"
        constant = "LOG_" + name.upper()
        return getattr(syslog, constant)

    priority = property(_get_priority)

    def _get_hosts(self):
        return [hostname.strip() for hostname in
                self._get_item(Config.HOSTS).split(",")]

    hosts = property(_get_hosts)
