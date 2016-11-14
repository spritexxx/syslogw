import logging

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

__author__ = 'Simon Esprit'


class MongoDBConnection(object):
    database = None

    def __init__(self, collection, host="localhost", port=27017):
        # collection in database where all messages will be stored
        self.collection = collection
        self.host = host
        self.port = port

    def connect(self):
        try:
            client = MongoClient(host=self.host, port=self.port)
            self.database = client.syslog
            return True
        except ConnectionFailure as e:
            logging.error("could not connect to mongod %s:%d" % (self.host, self.port))
            return False

    def store_message_data(self, message_data):
        """
        Store SyslogData in a collection in the database.
        :param message_data: SyslogData object that will be stored.
        """
        if self.database is None:
            logging.error("no database connection made yet")
            return None

        col = self.database[self.collection]

        post = message_data.message.as_dict()
        # store these extra fields in the DB as well
        post['rx_timestamp'] = message_data.timestamp
        post['origin_ip'] = message_data.origin_ip

        return col.insert_one(post)
