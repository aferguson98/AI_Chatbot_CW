"""
Chat.py
"""
import re
from difflib import SequenceMatcher

from AKOBot import NLPEngine
from Database.DatabaseConnector import DBConnection
from akobot import StationNoMatchError, StationNotFoundError


class Chat:
    def __init__(self):
        self.chat_log = []
        self.db_connection = DBConnection('AKODatabase.db')
        self.nlp_engine = NLPEngine()

    def add_message(self, author, message_text, time):
        self.chat_log.append({
            "author": author,
            "message_text": message_text,
            "time": time
        })


class Booking(Chat):
    def __init__(self, allow_advance_fare=True, class_of_travel='S',
                 has_railcard=False, is_return=False, num_adults=1,
                 num_children=1, super_class=None):
        """

        Parameters
        ----------
        allow_advance_fare: boolean
            Whether to allow advance fares to be included in the search for the
            cheapest fares (default: True)
        class_of_travel: str
            The class of travel the booking will be in - either 'S' for standard
            class or 'F' for first class (default: 'S')
        has_railcard: boolean
            If the booking has a railcard attached to it (True) or not (False)
            (default: False)
        is_return: boolean
            True if a return ticket is required, else False (default: False)
        num_adults: int
            Number of adult tickets to purchase (default: 1)
        num_children: int
            Number of child tickets to purchase (default: 0)
        super_class: type of Chat
            An instance of a Chat object which is being used as a basis of this
            instance of booking - the chat_log, db_connection and nlp_engine
            variables will be copied to this instance. (default: None)
        """
        super().__init__()
        self.allow_advance_fare = allow_advance_fare
        self.arrival = None
        self.class_of_travel = class_of_travel
        self.departure = None
        self.has_railcard = has_railcard
        self.is_return = is_return
        self.num_adults = num_adults
        self.num_children = num_children
        if isinstance(super_class, Chat):
            self.chat_log = super_class.chat_log
            self.db_connection = super_class.db_connection
            self.nlp_engine = super_class.nlp_engine

    @staticmethod
    def get_similarity(comparator_a, comparator_b):
        """

        Parameters
        ----------
        comparator_a: tuple
            The tuple from the database when searching for identifier, name
            from main.Stations table
        comparator_b: str
            The departure point input by the user
        Returns
        -------
        float
            The SequenceMatcher produced ration between the station name from
            the database and the departure point passed in by the user
        """
        comparator_a = comparator_a[1].replace("(" + comparator_b + ")", "")
        return SequenceMatcher(None, comparator_a[1], comparator_b).ratio()

    def add_departure(self, departure_station):
        query = ("SELECT identifier FROM main.Stations WHERE identifier=?"
                 " COLLATE NOCASE")
        result = self.db_connection.send_query(query,
                                               (departure_station,)).fetchall()
        if result:
            self.departure = departure_station
        else:
            # Station code not input - try searching by station name
            query = ("SELECT identifier FROM main.Stations WHERE name=?"
                     " COLLATE NOCASE")
            result = self.db_connection.send_query(query,
                                                   (departure_station,)
                                                   ).fetchall()
            if result and len(result) == 1:
                self.departure = result[0][0]
            else:
                # Try finding stations with names close to input name
                query = ("SELECT * FROM main.Stations WHERE name LIKE ? "
                         "COLLATE NOCASE")
                result = self.db_connection.send_query(
                    query, ("%" + departure_station + "%",)).fetchall()
                if result:
                    result.sort(key=lambda station: self.get_similarity(
                        station, departure_station), reverse=True)
                    if len(result) <= 3:
                        raise StationNoMatchError(result)
                    else:
                        raise StationNoMatchError(result[0:3])
                else:
                    msg = "Unable to find station {}"
                    raise StationNotFoundError(msg.format(departure_station))
