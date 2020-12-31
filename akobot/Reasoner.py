"""
Reasoner.py

Contains classes related to reasoning
"""
from difflib import SequenceMatcher

from experta import *
from spacy.matcher import Matcher

from Database.DatabaseConnector import DBConnection
from akobot import StationNoMatchError, StationNotFoundError
from akobot.AKOBot import NLPEngine

TokenDictionary = {
    "book": [{"LEMMA": {"IN": ["book", "booking", "purchase", "buy"]}}],
    "delay": [{"LEMMA": {"IN": ["delay", "predict", "prediction"]}}],
    "help": [{"LEMMA": {"IN": ["help", "support", "assistance"]}}],
    "yes": ["yes", "yeah", "y", "yep", "yeh", "ye"],
    "no": ["no", "nope", "n", "nah", "na"],
    "depart": [{"POS": "ADP", "LEMMA": {"IN": ["depart", "from", "departing"]}},
               {"POS": "PROPN", "OP": "+"}, {"POS": "PROPN", "DEP": "pobj"}],
    "arrive": [{"POS": "ADP", "LEMMA": {"IN": ["arrive", "to", "arriving"]}},
               {"POS": "PROPN", "OP": "*"}, {"POS": "PROPN", "DEP": "pobj"}],

}


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
    ratio = SequenceMatcher(None, comparator_a.lower(),
                            comparator_b.lower()).ratio() * 100
    if comparator_b.lower() in comparator_a.lower():
        ratio += 25
    if comparator_b.lower().startswith(comparator_a.lower()):
        ratio += 25
    return ratio


class ChatEngine(KnowledgeEngine):
    def __init__(self):
        super().__init__()

        # Internal connections to AKOBot classes
        self.db_connection = DBConnection('AKODatabase.db')
        self.nlp_engine = NLPEngine()

        # User Interface output
        self.message = ("I'm sorry. I don't know how to help with that just "
                        "yet. Please try again")
        self.suggestions = []

    def get_matches(self, doc, pattern):
        matcher = Matcher(self.nlp_engine.nlp.vocab)
        matcher.add("pattern", None, pattern)
        matches = matcher(doc)
        if len(matches) > 0:
            for match_id, start, end in matches:
                return doc[start:end]
        return None

    def find_station(self, search_station):
        query = ("SELECT identifier, name FROM main.Stations WHERE identifier=?"
                 " COLLATE NOCASE")
        result = self.db_connection.send_query(query,
                                               (search_station,)).fetchall()
        if result:
            return result[0]
        else:
            # Station code not input - try searching by station name
            query = ("SELECT identifier, name FROM main.Stations WHERE  name=? "
                     "COLLATE NOCASE")
            result = self.db_connection.send_query(query,
                                                   (search_station,)
                                                  ).fetchall()
            if result and len(result) == 1:
                return result[0]
            else:
                # Try finding stations with names close to input name
                query = "SELECT * FROM main.Stations"
                result = self.db_connection.send_query(query).fetchall()
                if result:
                    result.sort(key=lambda station: get_similarity(
                        station, search_station), reverse=True)
                    if len(result) <= 3:
                        raise StationNoMatchError(result)
                    else:
                        raise StationNoMatchError(result[0:3])
                else:
                    msg = "Unable to find station {}"
                    raise StationNotFoundError(msg.format(search_station))

    @DefFacts()
    def _initial_action(self):
        self.message = ("I'm sorry. I don't know how to help with that just "
                        "yet. Please try again")
        self.suggestions = []
        yield Fact(action="chat")

    @Rule(AS.f1 << Fact(action="chat"),
          Fact(message_text=MATCH.message_text))
    def direct_to_correct_action(self, f1, message_text):
        """
        Directs the engine to the correct action for the message text passed

        Parameters
        ----------
        f1: Fact
            The Fact containing the current action
        message_text: str
            The message text passed by the user to the Chat class
        """
        doc = self.nlp_engine.process(message_text)
        matcher = Matcher(self.nlp_engine.nlp.vocab)
        matcher.add("BOOKING_PATTERN", None, TokenDictionary['book'])
        matches = matcher(doc)
        if len(matches) > 0:
            # likely to be a booking
            self.message = "Ok great, let's get your booking started!"
            self.suggestions = []
            self.modify(f1, action="book")
            self.declare(Fact(complete=False))
            self.declare(Fact(extra_info_req=False))
        else:
            matcher.add("DELAY_PATTERN", None, TokenDictionary['delay'])
            matches = matcher(doc)
            if len(matches) > 0:
                # likely to be a delay prediction
                self.message = ("Using the latest train data, I can predict "
                                "how long you'll be delayed.")
                self.suggestions = []
                self.modify(f1, action="delay")
            else:
                matcher.add("HELP_PATTERN", None, TokenDictionary['help'])
                matches = matcher(doc)
                if len(matches) > 0:
                    # likely to be a support request
                    self.message = "Ok, no problem! I'm here to help."
                    self.suggestions = []
                    self.modify(f1, action="help")

    # BOOKING ACTIONS
    @Rule(Fact(action="book"),
          AS.f1 << Fact(complete=False),
          AS.f2 << Fact(extra_info_req=False),
          Fact(message_text=MATCH.message_text))
    def booking_not_complete(self, f1, f2, message_text):
        """
        If a booking is not ready to be passed to web scraping stage, check if
        any new information has been provided to make booking complete

        Parameters
        ----------
        f1: Fact
            The Fact representing whether the booking is complete or not

        f2: Fact
            The Fact representing whether the bot needs to request extra info
            to complete this booking

        message_text: str
            The message text passed by the user to the Chat class
        """
        doc = self.nlp_engine.process(message_text)

        # Departure Station
        dep = self.get_matches(doc, TokenDictionary["depart"])
        if dep is not None:
            search_station = str(dep[1:])
            try:
                station = self.find_station(search_station)
                self.message = "Your departure point is: " + station[1]
                self.suggestions = []
            except StationNoMatchError as e:
                self.message = ("I found a few departure stations that matched"
                                "that name. Is one of these correct?")
                self.suggestions = ["{TAG:DEP}" + alternative[1]
                                    for alternative in e.alternatives]
            except StationNotFoundError as e:
                self.message = ("I couldn't find any departure stations with "
                                "that name. Please try again.")
                self.suggestions = []

        # Departure Station
        arr = self.get_matches(doc, TokenDictionary["arrive"])
        if arr is not None:
            search_station = str(arr[1:])
            try:
                station = self.find_station(search_station)
                self.message = "Your arrival point is: " + station[1]
                self.suggestions = []
            except StationNoMatchError as e:
                self.message = ("I found a few arrival stations that matched"
                                "that name. Is one of these correct?")
                self.suggestions = ["{TAG:DEP}" + alternative[1]
                                    for alternative in e.alternatives]
            except StationNotFoundError as e:
                self.message = ("I couldn't find any arrival stations with "
                                "that name. Please try again.")
                self.suggestions = []

    # # Request Extra Info # #
    @Rule(Fact(action="book"),
          AS.f1 << Fact(extra_info_req=True),
          NOT(Fact(depart=W())))
    def ask_for_departure(self, f1):
        """Decides if need to ask user for the departure point"""
        self.message = "And where are you travelling from?"
        self.suggestions = []

    # DELAY ACTIONS

    # HELP ACTIONS
