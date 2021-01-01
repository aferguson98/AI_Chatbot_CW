"""
Reasoner.py

Contains classes related to reasoning
"""
from difflib import SequenceMatcher

from experta import *
from spacy.matcher import Matcher

from Database.DatabaseConnector import DBConnection
from akobot import StationNoMatchError, StationNotFoundError, \
    UnknownPriorityException
from akobot.AKOBot import NLPEngine

TokenDictionary = {
    "book": [{"LEMMA": {"IN": ["book", "booking", "purchase", "buy"]}}],
    "delay": [{"LEMMA": {"IN": ["delay", "predict", "prediction"]}}],
    "help": [{"LEMMA": {"IN": ["help", "support", "assistance"]}}],
    "yes": ["yes", "yeah", "y", "yep", "yeh", "ye"],
    "no": ["no", "nope", "n", "nah", "na"],
    "depart": [{"POS": "ADP", "LEMMA": {"IN": ["depart", "from", "departing"]}},
               {"POS": "PROPN", "OP": "*"}, {"POS": "PROPN", "DEP": "pobj"}],
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

        # Knowledge dict
        self.knowledge = {}

        # User Interface output
        self.def_message = {"message": "I'm sorry. I don't know how to help "
                                       "with that just yet. Please try again",
                            "suggestions": [],
                            "response_req": True}
        self.message = []

    def get_matches(self, doc, pattern):
        matcher = Matcher(self.nlp_engine.nlp.vocab)
        matcher.add("pattern", None, pattern)
        matches = matcher(doc)
        if len(matches) > 0:
            for match_id, start, end in matches:
                return doc[start:end]
        return None

    def add_to_message_chain(self, message, priority=1, req_response=True,
                             suggestions=None):
        """

        Parameters
        ----------
        message: str
            The message to add to the queue
        priority: int
            A priority value. 1 = Standard, 0 = High, 7 = Tag. A high priority
            message will be added to start of the queue and standard priority
            to the end. A tag message will be added to the start of the first
            message in the queue
        req_response
        suggestions
        """
        if suggestions is None:
            suggestions = []
        if (len(self.message) == 1 and
                self.def_message in self.message and
                priority != 7):
            self.message = []
        if "I found" in message and len(self.message) > 0:
            message = message.replace("I found", "I also found")
        if priority == 1:
            self.message.append({"message": message,
                                 "suggestions": suggestions,
                                 "response_req": req_response})
        elif priority == 0:
            self.message.insert(0, {"message": message,
                                    "suggestions": suggestions,
                                    "response_req": req_response})
        elif priority == 7:
            self.message[0]['message'] = message + self.message[0]['message']
        else:
            raise UnknownPriorityException(priority)

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
        if len(self.message) == 0:
            self.message = [self.def_message]
        for key, value in self.knowledge.items():
            this_fact = {key: value}
            yield Fact(**this_fact)
        if "action" not in self.knowledge.keys():
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
            self.add_to_message_chain("Ok great, let's get your booking "
                                      "started! I'll put all the details on the"
                                      " right hand side as we go.",
                                      req_response=False)
            self.modify(f1, action="book")
            self.declare(Fact(complete=False))
            self.declare(Fact(extra_info_req=False))
        else:
            matcher.add("DELAY_PATTERN", None, TokenDictionary['delay'])
            matches = matcher(doc)
            if len(matches) > 0:
                # likely to be a delay prediction
                self.add_to_message_chain("Using the latest train data, I can "
                                          "predict how long you'll be delayed.",
                                          req_response=False)
                self.modify(f1, action="delay")
            else:
                matcher.add("HELP_PATTERN", None, TokenDictionary['help'])
                matches = matcher(doc)
                if len(matches) > 0:
                    # likely to be a support request
                    self.add_to_message_chain("Ok, no problem! I'm here to "
                                              "help.", req_response=False)
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
        message = ""

        # Departure Station
        dep_found_mul_msg = ("I found a few departure stations that matched {}."
                             " Is one of these correct?")
        dep_found_none_msg = ("I couldn't find any departure stations "
                              "matching {}. Please try again.")

        dep = self.get_matches(doc, TokenDictionary["depart"])
        if dep is not None:
            search_station = str(dep[1:])
            try:
                station = self.find_station(search_station)
                message += "{DEP:" + station[1] + "}"
                self.declare(Fact(depart=station[0]))
            except StationNoMatchError as e:
                self.add_to_message_chain(
                    dep_found_mul_msg.format(search_station),
                    suggestions=["{TAG:DEP}" + alternative[1]
                                 for alternative in e.alternatives]
                )
            except StationNotFoundError as e:
                self.add_to_message_chain(
                    dep_found_none_msg.format(search_station)
                )
        elif "{TAG:DEP}" in message_text:
            search_station = message_text.replace("{TAG:DEP}", "")
            try:
                station = self.find_station(search_station)
                message += "{DEP:" + station[1] + "}"
                self.suggestions = []
                self.declare(Fact(depart=station[0]))
            except StationNoMatchError as e:
                self.add_to_message_chain(
                    dep_found_mul_msg.format(search_station),
                    suggestions=["{TAG:DEP}" + alternative[1]
                                 for alternative in e.alternatives]
                )
            except StationNotFoundError as e:
                self.add_to_message_chain(
                    dep_found_none_msg.format(search_station)
                )

        # Arrival Station
        arr_found_mul_msg = ("I found a few arrival stations that matched {}."
                             " Is one of these correct?")
        arr_found_none_msg = ("I couldn't find any arrival stations "
                              "matching {}. Please try again.")

        arr = self.get_matches(doc, TokenDictionary["arrive"])
        print(arr)
        if arr is not None:
            search_station = str(arr[1:])
            try:
                station = self.find_station(search_station)
                message += "{ARR:" + station[1] + "}"
                self.declare(Fact(arrive=station[0]))
            except StationNoMatchError as e:
                self.add_to_message_chain(
                    arr_found_mul_msg.format(search_station),
                    suggestions=["{TAG:ARR}" + alternative[1]
                                 for alternative in e.alternatives]
                )
            except StationNotFoundError as e:
                self.add_to_message_chain(
                    arr_found_none_msg.format(search_station)
                )
        elif "{TAG:ARR}" in message_text:
            search_station = message_text.replace("{TAG:ARR}", "")
            try:
                station = self.find_station(search_station)
                message += "{ARR:" + station[1] + "}"
                self.declare(Fact(arrive=station[0]))
            except StationNoMatchError as e:
                self.add_to_message_chain(
                    arr_found_mul_msg.format(search_station),
                    suggestions=["{TAG:ARR}" + alternative[1]
                                 for alternative in e.alternatives]
                )
            except StationNotFoundError as e:
                self.add_to_message_chain(
                    arr_found_none_msg.format(search_station)
                )
        self.add_to_message_chain(message, priority=7)

    # # Request Extra Info # #
    @Rule(Fact(action="book"),
          AS.f1 << Fact(extra_info_req=True),
          NOT(Fact(depart=W())))
    def ask_for_departure(self, f1):
        """Decides if need to ask user for the departure point"""
        self.message = "And where are you travelling from?"

    # DELAY ACTIONS

    # HELP ACTIONS

    @Rule()
    def add_all_facts_to_dict(self):
        for f in self.facts:
            for g, val in self.facts[f].items():
                if g != "__factid__" and g != "message_text":
                    self.knowledge[g] = val
