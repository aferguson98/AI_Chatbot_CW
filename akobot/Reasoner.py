"""
Reasoner.py

Contains classes related to reasoning
"""
from datetime import datetime
from difflib import SequenceMatcher
from experta import *

import time

from spacy.matcher import Matcher

from akobot.AKOBot import NLPEngine
from Database.DatabaseConnector import DBConnection
from akobot import StationNoMatchError, StationNotFoundError

TokenDictionary = {
    "book": [{"LEMMA": {"IN": ["book", "booking", "purchase", "buy"]}}],
    "delay": [{"LEMMA": {"IN": ["delay", "predict", "prediction"]}}],
    "help": [{"LEMMA": {"IN": ["help", "support", "assistance"]}}],
    "yes": ["yes", "yeah", "y", "yep", "yeh", "ye"],
    "no": ["no", "nope", "n", "nah", "na"],
    "depart": ["depart", "from", "departing"],
    "arrive": ["arrive", "to", "arriving"],

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

    @DefFacts()
    def _initial_action(self):
        yield Fact(action="chat")

    @Rule(Fact(action="chat"),
          Fact(message_text=MATCH.message_text))
    def direct_to_correct_action(self, message_text):
        """
        Directs the engine to the correct action for the message text passed

        Parameters
        ----------
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
            self.modify(self.facts, action="book")
            self.declare(Fact(complete=False))
        else:
            matcher.add("DELAY_PATTERN", None, TokenDictionary['delay'])
            matches = matcher(doc)
            if len(matches) > 0:
                # likely to be a delay prediction
                self.message = ("Using the latest train data, I can predict "
                                "how long you'll be delayed.")
                self.suggestions = []
                self.retract(Fact(action="chat"))
                self.declare(Fact(action="delay"))
            else:
                matcher.add("HELP_PATTERN", None, TokenDictionary['help'])
                matches = matcher(doc)
                if len(matches) > 0:
                    # likely to be a support request
                    self.message = "Ok, no problem! I'm here to help."
                    self.suggestions = []
                    self.declare(Fact(action="help"))
                    return

    # BOOKING ACTIONS
    @Rule(Fact(action="book"),
          NOT(Fact(complete=True)),
          Fact(message_text=MATCH.message_text))
    def booking_not_complete(self, message_text):
        """
        If a booking is not ready to be passed to web scraping stage, check if
        any new information has been provided to make booking complete

        Parameters
        ----------
        message_text: str
            The message text passed by the user to the Chat class
        """

    @Rule(Fact(action="book"),
          NOT(Fact(depart=W())))
    def ask_for_departure(self):
        """Decides if need to ask user for the departure point"""
        self.message = "Ok, no problem! Where are you travelling from?"
        self.suggestions = []

    # DELAY ACTIONS

    # HELP ACTIONS