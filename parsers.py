import abc
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

    def parse_message(self, parser=None):
        """
        Try to parse raw data to a SyslogMessage
        :param parser: force usage of a specific Parser.
        :return: SyslogMessage or None in case it could not be parsed.
        """
        if parser is not None:
            parsed = parser.parse_message(self.message)
            if not parsed:
                logging.warn("%s could not parse: %s" % (parser.__name__, self.message))
        else:
            message = RFC5424Parser.parse_message(self.message)
            if message is not None:
                return message

            # try all known NonRFC5424 parsers
            for subclass in NonRFC5424Parser.__subclasses__():
                message = subclass.parse_message(self.message)
                if message is not None:
                    return message

            return None


class Parser(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def parse_message(self, data):
        """Parse message with class specific format """

    @abc.abstractmethod
    def name(self):
        """Name by which this parser can be selected from command line"""


class RFC5424Parser(Parser):
    @staticmethod
    def name():
        return "rfc5424"

    """
    Parses messages that conform to RFC5424 specification.
    """
    @classmethod
    def parse_message(cls, data):
        try:
            message = SyslogMessage.parse(data)
        except ParseError as e:
            message = None
            logging.warning("%s - %s" % (cls.__name__, str(e)))

        return message


class NonRFC5424Parser(Parser):
    """
    Internal classes for use by non-RFC parser.
    Contains class definitions and helper functions that can be used by implementers.
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
    def name():
        pass

    @staticmethod
    def _toInt(s, loc, toks):
        return int(toks[0])

    @classmethod
    def parse_message(cls, data):
        pass


class BusyboxParser(NonRFC5424Parser):
    """
    Parses syslog messages sent by syslogd as found in Busybox.
    This version is often found in embedded devices and is NOT RFC5424 compliant.
    """
    @staticmethod
    def name():
        return "busybox"

    @staticmethod
    def _pyparse_message(string):
        """
        Parse message string using pyparse.
        """
        # pyparse variables
        dash = Literal("-")
        colon = Literal(":")
        SP = Suppress(White(ws=' ', min=1, max=1))

        pri = Combine(Suppress(Literal("<")) + Word(nums, min=1, max=3) + Suppress(Literal(">"))).setParseAction(NonRFC5424Parser._toInt)

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

    @classmethod
    def parse_message(cls, data):
        try:
            groups = BusyboxParser._pyparse_message(data)
        except ParseException as e:
            logging.debug("%s - %s" % (cls.__name__, str(e)))
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
            facility = NonRFC5424Parser.SyslogFacility(facility)
        except Exception:
            facility = NonRFC5424Parser.SyslogFacility.unknown

        severity = pri & 7
        severity = NonRFC5424Parser.SyslogSeverity(severity)

        return SyslogMessage(severity=severity, facility=facility, timestamp=timestamp, appname=appname, msg=message)


class OSXParser(NonRFC5424Parser):
    """
    Parses syslog messages sent by syslogd as found in OSX (Apple).
    Note that the default format is expected.
    """
    @staticmethod
    def name():
        return "macosx"

    @staticmethod
    def _pyparse_message(string):
        """
        Parse message string using pyparse.
        """
        # pyparse variables
        dash = Literal("-")
        colon = Literal(":")
        SP = Suppress(White(ws=' ', min=1, max=1))

        pri = Combine(Suppress(Literal("<")) + Word(nums, min=1, max=3) + Suppress(Literal(">"))).setParseAction(NonRFC5424Parser._toInt)

        rfc3164_date = Word(alphas, min=3, max=3) + SP + Word(nums, min=2, max=2)
        rfc3164_time = Combine(Word(nums, min=2, max=2) + colon + Word(nums, min=2, max=2) + colon + Word(nums, min=2, max=2))

        # hostname from originator - not sure how long this can be!
        hostname = Word(printables, min=1, max=255)

        # TODO must support apps which contain spaces on OSX
        appname = Word(alphanums, min=1, max=48)
        procid = Combine(Suppress(Literal("[")) + Word(alphanums, min=1, max=128) + Suppress(Literal("]"))).setParseAction(NonRFC5424Parser._toInt)

        header = Group(
            pri.setResultsName('pri') +
            rfc3164_date.setResultsName('date') + SP +
            rfc3164_time.setResultsName('time') + SP +
            hostname.setResultsName('host') + SP +
            appname.setResultsName('appname') +
            procid.setResultsName('procid') + colon
        )

        message = Combine(restOfLine + lineEnd)
        syslog_message = header.setResultsName('header') + Optional(SP + message.setResultsName('message'))

        return syslog_message.parseString(string)

    @classmethod
    def parse_message(cls, data):
        try:
            groups = OSXParser._pyparse_message(data)
        except ParseException as e:
            logging.debug("%s - %s" % (cls.__name__, str(e)))
            return None

        header = groups['header']

        time = header['time']
        date = header['date']
        timestamp = "%s-%sT%s.00Z" % (date[0], date[1], time)

        host = header['host']
        appname = header['appname']
        procid = header['procid']

        if 'message' in groups:
            message = groups['message']
        else:
            message = None

        pri = int(header['pri'])

        facility = pri >> 3
        try:
            facility = NonRFC5424Parser.SyslogFacility(facility)
        except Exception:
            facility = NonRFC5424Parser.SyslogFacility.unknown

        severity = pri & 7
        severity = NonRFC5424Parser.SyslogSeverity(severity)

        return SyslogMessage(severity=severity, facility=facility, timestamp=timestamp,
                             hostname=host, appname=appname, procid=procid,
                             msg=message)
