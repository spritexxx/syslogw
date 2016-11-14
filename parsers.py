import abc
import json
import logging
import time

from enum import IntEnum

from pyparsing import Optional, Literal, QuotedString, Word, Or, ZeroOrMore, OneOrMore, White, Group, Combine, Suppress
from pyparsing import nums, alphas, printables, restOfLine, lineEnd, ParseException, alphanums

from syslog_rfc5424_parser import SyslogMessage, ParseError

__author__ = 'Simon Esprit'


class RawSyslogData(object):
    """
    Holds unparsed syslog data.
    """
    def __init__(self, message, origin_ip):
        self.message = message
        self.origin_ip = str(origin_ip)
        self.timestamp = time.time() * 1000


class SyslogData(object):
    """
    Holds a parsed SyslogMessage along with extra info.
    """
    def __init__(self, message, origin_ip, timestamp):
        """
        Create new SyslogData container object.
        :param message: a SyslogMessage
        :param origin_ip: origin IP address (String)
        :param timestamp: ms since epoch when this message was received (not parsed!)
        """
        self.message = message
        self.origin_ip = origin_ip
        self.timestamp = timestamp


class Parser(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def parse_message(self, data):
        """Parse message with class specific format """


class RFC5424Parser(Parser):
    """
    Parses messages that conform to RFC5424 specification.
    """
    @staticmethod
    def parse_message(data):
        try:
            message = SyslogMessage.parse(data)
        except ParseError as e:
            message = None
            logging.warning("Could not parse message: " + str(e))

        return message


class BusyboxParser(Parser):
    """
    Parses syslog messages sent by syslogd as found in Busybox.
    This version is often found in embedded devices and is NOT RFC5424 compliant.
    """

    class SyslogFacility(IntEnum):
        kern = 0
        user = 1
        mail = 2
        daemon = 3
        auth = 4
        syslog = 5
        lpr = 6
        news = 7
        uucp = 8
        cron = 9
        authpriv = 10
        ftp = 11
        ntp = 12
        audit = 13
        alert = 14
        clockd = 15
        local0 = 16
        local1 = 17
        local2 = 18
        local3 = 19
        local4 = 20
        local5 = 21
        local6 = 22
        local7 = 23
        unknown = -1

    class SyslogSeverity(IntEnum):
        emerg = 0
        alert = 1
        crit = 2
        err = 3
        warning = 4
        notice = 5
        info = 6
        debug = 7

    @staticmethod
    def _toInt(s, loc, toks):
        return int(toks[0])

    @staticmethod
    def _pyparse_message(string):
        """
        Parse message string using pyparse.
        """
        # pyparse variables
        dash = Literal("-")
        colon = Literal(":")
        SP = Suppress(White(ws=' ', min=1, max=1))

        pri = Combine(Suppress(Literal("<")) + Word(nums, min=1, max=3) + Suppress(Literal(">"))).setParseAction(BusyboxParser._toInt)

        rfc3164_date = Word(alphas, min=3, max=3) + SP + Word(nums, min=2, max=2)
        rfc3164_time = Combine(Word(nums, min=2, max=2) + colon + Word(nums, min=2, max=2) + colon + Word(nums, min=2, max=2))

        # not clear what this represents...
        appname = Word(alphanums, min=1, max=48)

        header = Group(
           pri.setResultsName('pri') +
           rfc3164_date.setResultsName('date') + SP +
           rfc3164_time.setResultsName('time') + SP +
           appname.setResultsName('appname') + colon
        )

        message = Combine(restOfLine + lineEnd)
        syslog_message = header.setResultsName('header') + Optional(SP + message.setResultsName('message'))

        return syslog_message.parseString(string)

    @staticmethod
    def parse_message(data):
        try:
            groups = BusyboxParser._pyparse_message(data)
        except ParseException as e:
            logging.warning("failed to parse syslog message: " + str(e))
            return None

        header = groups['header']

        time = header['time']
        date = header['date']
        timestamp = "%s-%sT%s.00Z" % (date[0], date[1], time)

        appname = header['appname']

        if 'message' in groups:
            message = groups['message']
        else:
            message = None

        pri = int(header['pri'])

        facility = pri >> 3
        try:
            facility = BusyboxParser.SyslogFacility(facility)
        except Exception:
            facility = BusyboxParser.SyslogFacility.unknown

        severity = pri & 7
        severity = BusyboxParser.SyslogSeverity(severity)

        return SyslogMessage(severity=severity, facility=facility, timestamp=timestamp, appname=appname, msg=message)
