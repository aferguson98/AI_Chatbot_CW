"""
Chat.py
"""
from AKOBot import NLPEngine
from Database.DatabaseConnector import DBConnection


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

    def add_departure(self, departure_station):
        query = "SELECT identifier FROM main.Stations WHERE identifier=?"
        if self.db_connection.send_query(query, (departure_station,)):
            self.departure = departure_station


if __name__ == '__main__':
    booking = Booking()
    booking.add_departure("NRW")
    print(booking.departure)
