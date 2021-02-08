"""
Reasoner.py

Contains classes related to reasoning
"""
import re
from datetime import datetime
from difflib import SequenceMatcher

from dateparser.date import DateDataParser
from dateutil.parser import parse, ParserError
from experta import *
from spacy.matcher import Matcher

from Database.DatabaseConnector import DBConnection
from DelayPrediction.newPrediction import Predictions
from akobot import (StationNoMatchError,
                    StationNotFoundError,
                    UnknownPriorityException,
                    UnknownStationTypeException,
                    scraper_1)
from akobot.AKOBot import NLPEngine, get_all_stations

TokenDictionary = {
    "book": [{"LEMMA": {"IN": ["book", "booking", "purchase", "buy"]}}],
    "delay": [{"LEMMA": {"IN": ["delay", "predict", "prediction"]}}],
    "yes": [{"LOWER": {"IN": ["yes", "yeah", "y", "yep", "yeh", "ye", "👍"]}}],
    "no": [{"LOWER": {"IN": ["no", "nope", "n", "nah", "na", "👎"]}}],
    "return": [{"LEMMA": {"IN": ["return", "returning"]}}],
    "single": [{"LEMMA": {"IN": ["single", "one-way"]}}],
    "dep_delay": [{"LIKE_NUM": True}],
    "num_adults": [{"LIKE_NUM": True}, {"LEMMA": "adult"}],
    "num_children": [{"LIKE_NUM": True}, {"LEMMA": "child"}]
}

MultiTokenDictionary = {
    "depart": [
        [{"POS": "ADP", "LEMMA": {"IN": ["depart", "from", "departing"]}},
         {"POS": "PROPN", "OP": "*"}, {"POS": "PROPN", "DEP": "pobj"}],
        [{"LEMMA": {"IN": ["depart", "from", "departing"]}},
         {"LOWER": {"IN": get_all_stations()}}]
    ],
    "arrive": [
        [{"POS": "ADP", "LEMMA": {"IN": ["arrive", "to", "arriving"]}},
         {"POS": "PROPN", "OP": "*"}, {"POS": "PROPN", "DEP": "pobj"}],
        [{"LEMMA": {"IN": ["arrive", "to", "arriving"]}},
         {"LOWER": {"IN": get_all_stations()}}]
    ],
    "dep_date": [
        [{"LEMMA": {"IN": ["depart", "departing", "leave", "leaving"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "DATE", "OP": "*"},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "TIME", "OP": "*"},
         {"ENT_TYPE": "TIME", "DEP": "pobj"}, {"ENT_TYPE": "TIME"}],
        [{"LEMMA": {"IN": ["depart", "departing", "leave", "leaving"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "DATE", "OP": "*"},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "TIME", "OP": "*"},
         {"ENT_TYPE": "TIME", "DEP": "pobj"}],
        [{"LEMMA": {"IN": ["depart", "departing", "leave", "leaving"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "TIME", "OP": "*"},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "DATE", "OP": "*"},
         {"ENT_TYPE": "DATE", "DEP": "pobj"}],
        [{"LEMMA": {"IN": ["depart", "departing", "leave", "leaving"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "DATE", "OP": "*"},
         {"POS": "ADP", "OP": "?"}, {"SHAPE": "dd:dd"}],
        [{"LEMMA": {"IN": ["depart", "departing", "leave", "leaving"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "DATE", "OP": "*"},
         {"POS": "ADP", "OP": "?"}, {"SHAPE": "dddd"}],
        [{"LEMMA": {"IN": ["depart", "departing", "leave", "leaving"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "DATE", "OP": "*"},
         {"POS": "ADP", "OP": "?"}, {"SHAPE": "d:dd"}],
        [{"LEMMA": {"IN": ["depart", "departing", "leave", "leaving"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "TIME", "OP": "*"},
         {"POS": "ADP", "OP": "?"}, {"SHAPE": "dd:dd"}],
        [{"LEMMA": {"IN": ["depart", "departing", "leave", "leaving"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "TIME", "OP": "*"},
         {"POS": "ADP", "OP": "?"}, {"SHAPE": "dddd"}],
        [{"LEMMA": {"IN": ["depart", "departing", "leave", "leaving"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "TIME", "OP": "*"},
         {"POS": "ADP", "OP": "?"}, {"SHAPE": "d:dd"}]
    ],
    "ret_date": [
        [{"LEMMA": {"IN": ["return", "returning"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "DATE", "OP": "*"},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "TIME", "OP": "*"},
         {"ENT_TYPE": "TIME", "DEP": "pobj"}],
        [{"LEMMA": {"IN": ["return", "returning"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "TIME", "OP": "*"},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "DATE", "OP": "*"},
         {"ENT_TYPE": "DATE", "DEP": "pobj"}],
        [{"LEMMA": {"IN": ["return", "returning"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "DATE", "OP": "*"},
         {"POS": "ADP", "OP": "?"}, {"SHAPE": "dd:dd"}],
        [{"LEMMA": {"IN": ["return", "returning"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "DATE", "OP": "*"},
         {"POS": "ADP", "OP": "?"}, {"SHAPE": "dddd"}],
        [{"LEMMA": {"IN": ["return", "returning"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "DATE", "OP": "*"},
         {"POS": "ADP", "OP": "?"}, {"SHAPE": "d:dd"}],
        [{"LEMMA": {"IN": ["return", "returning"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "TIME", "OP": "*"},
         {"POS": "ADP", "OP": "?"}, {"SHAPE": "dd:dd"}],
        [{"LEMMA": {"IN": ["return", "returning"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "TIME", "OP": "*"},
         {"POS": "ADP", "OP": "?"}, {"SHAPE": "dddd"}],
        [{"LEMMA": {"IN": ["return", "returning"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "TIME", "OP": "*"},
         {"POS": "ADP", "OP": "?"}, {"SHAPE": "d:dd"}]
    ],
    "dly_date": [
        [{"LEMMA": {"IN": ["depart", "departing", "leave", "leaving"]}},
         {"POS": "ADP", "OP": "?"}, {"SHAPE": "dd:dd"}],
        [{"LEMMA": {"IN": ["depart", "departing", "leave", "leaving"]}},
         {"POS": "ADP", "OP": "?"}, {"SHAPE": "d:dd"}],
        [{"LEMMA": {"IN": ["depart", "departing", "leave", "leaving"]}},
         {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "TIME", "OP": "*"},
         {"ENT_TYPE": "TIME", "DEP": "pobj"}]
    ]
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
        self.progress = ""

        # User Interface output
        self.def_message = {"message": "I'm sorry. I don't know how to help "
                                       "with that just yet. Please try again",
                            "suggestions": [],
                            "response_req": True}
        self.message = []
        self.tags = ""

    def declare(self, *facts):
        """
        Overrides super class' method declare to add the facts to the knowledge
        dictionary (self.knowledge)
        """
        new_fact = super().declare(*facts)
        if new_fact:
            for g, val in new_fact.items():
                if g not in ["__factid__", "message_text", "extra_info_req",
                             "extra_info_requested"]:
                    self.knowledge[g] = val
        return new_fact

    def get_matches(self, doc, pattern):
        matcher = Matcher(self.nlp_engine.nlp.vocab)
        matcher.add("pattern", None, pattern)
        matches = matcher(doc)
        if len(matches) > 0:
            for match_id, start, end in matches:
                return doc[start:end]
        return None

    def get_matches_from_multiple(self, doc, pattern_arr):
        matches = None
        for pattern in pattern_arr:
            matches = self.get_matches(doc, pattern)
            if matches:
                break
        return matches

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
        if len(self.message) > 0 and "I found" in message:
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
            self.tags += message
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
            query = ("SELECT identifier, name FROM main.Stations WHERE name=? "
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

    def get_date_from_text(self, date_text, st_type="DEP"):
        date_text = date_text.replace(" am", "am")
        date_text = date_text.replace(" AM", "am")
        date_text = date_text.replace(" pm", "pm")
        date_text = date_text.replace(" PM", "pm")
        date_text = date_text.replace(" o'clock", ":00")
        date_text = date_text.replace(" oclock", ":00")
        date_text = date_text.replace("o'clock", ":00")
        date_text = date_text.replace("oclock", ":00")
        try:
            parse(date_text, fuzzy=True)
        except ParserError:
            return None
        else:
            ddp = DateDataParser(languages=['en'],
                                 settings={'DATE_ORDER': 'DMY'})
            date_time = ddp.get_date_data(date_text).date_obj
            date_time_now = datetime.now()
            if date_time and date_time <= date_time_now and st_type != "DLY":
                return 2
            if (("departure_date" in self.knowledge and
                    date_time <= self.knowledge['departure_date']) or
                    ("return_date" in self.knowledge and
                     date_time >= self.knowledge['return_date'])):
                return 1
            return date_time

    def get_dep_arr_station(self, doc, message_text, tags, st_type,
                            extra_info_appropriate=True, station_name = 0):
        """
        Get the arrival or departure station from the message_text and return
        the relevant tags and if extra info can be asked for

        Parameters
        ----------
        doc: spacy.Doc
            The Doc object created by passing the message_text through SpaCy's
            NLP tokeniser
        message_text: str
            The message text input by the user
        tags: list of str
            List of control tags to pass to the frontend to display relevant
            feedback to the user
        st_type: str
            The station type (departure or arrival) that is being searched for
            MUST be either "DEP" (departure) or "ARR" (arrival)
            default: "DEP"
        extra_info_appropriate: bool
            True if the user can be asked for extra information or False if it's
            not appropriate
            default: True
        Returns
        -------
        list of str
            The list of control tags to be passed to the frontend
        bool
            True if extra info can be asked for from the user and false if not
        """
        if st_type == "DEP":
            # Departure Station
            found_mul_msg = ("I found a few departure stations that matched {}."
                             " Is one of these correct?")
            found_none_msg = ("I couldn't find any departure stations matching "
                              "{}. Please try again.")
            progress_tag = "dl_"
            token = "depart"
            op_token = "arrive"
            noun_form = "departure"
        elif st_type == "ARR":
            # Arrival Station
            found_mul_msg = ("I found a few arrival stations that matched {}."
                             " Is one of these correct?")
            found_none_msg = ("I couldn't find any arrival stations matching {}"
                              ". Please try again.")
            progress_tag = "al_"
            token = "arrive"
            op_token = "depart"
            noun_form = "arrival"
        else:
            raise UnknownStationTypeException(st_type)

        search_station = None
        matches = self.get_matches_from_multiple(doc,
                                                 MultiTokenDictionary[token])

        if matches is not None:
            search_station = str(matches[1:])
        elif "{TAG:" + st_type + "}" in message_text:
            # the user has selected one of the selections which will be correct
            search_station = message_text.replace("{TAG:" + st_type + "}", "")

        if search_station:
            try:
                station = self.find_station(search_station)
                if (token in self.knowledge and
                        station[station_name] == self.knowledge[token]):
                    request_tag = "{REQ:" + st_type + "}"
                    msg = ("{}The departure and arrival station cannot be the "
                           "same. Please enter a new {} station")
                    self.add_to_message_chain(msg.format(request_tag, 
                                                         noun_form))
                    extra_info_appropriate = False
                else:
                    tags += "{" + st_type + ":" + station[1] + "}"
                    if st_type == "DEP":
                        self.declare(Fact(depart=station[station_name]))
                    else:
                        self.declare(Fact(arrive=station[station_name]))
                self.progress = self.progress.replace(progress_tag, "")
            except StationNoMatchError as e:
                extra_info_appropriate = False
                self.add_to_message_chain(
                    found_mul_msg.format(search_station),
                    suggestions=["{TAG:" + st_type + "}" + alternative[1]
                                 for alternative in e.alternatives]
                )
            except StationNotFoundError as e:
                extra_info_appropriate = False
                self.add_to_message_chain(
                    found_none_msg.format(search_station)
                )

        return tags, extra_info_appropriate

    def get_if_return(self, doc, message_text, tags, extra_info_appropriate):
        if "{TAG:RET}" in message_text:
            ret = self.get_matches(doc, TokenDictionary['yes'])
            if ret is None:
                ret = self.get_matches(doc, TokenDictionary['return'])
            sgl = self.get_matches(doc, TokenDictionary['no'])
            if sgl is None:
                sgl = self.get_matches(doc, TokenDictionary['single'])
        else:
            ret = self.get_matches(doc, TokenDictionary['return'])
            sgl = self.get_matches(doc, TokenDictionary['single'])
        if ret is not None and sgl is None:
            tags += "{RET:RETURN}"
            self.declare(Fact(returning=True))
            self.progress = self.progress.replace("rs_", "")
        elif sgl is not None and ret is None:
            tags += "{RET:SINGLE}{RTM:N/A}"
            self.declare(Fact(returning=False))
            self.progress = self.progress.replace("rs_", "")
            self.progress = self.progress.replace("rt_", "")
        elif sgl is not None and ret is not None:
            self.add_to_message_chain("{REQ:RET}Sorry, I don't understand. "
                                      "Are you returning? Try answering YES or "
                                      "NO.", 0, suggestions=["{TAG:RET} Yes",
                                                             "{TAG:RET} No"])
            extra_info_appropriate = False
        return tags, extra_info_appropriate

    def get_dep_arr_date(self, message_text, tags, st_type="DEP",
                         extra_info_appropriate=True):
        if st_type not in ["DEP", "RET", "DLY"]:
            raise UnknownStationTypeException(st_type)

        # replace times to be useful to SpaCy
        if (message_text.find("am") > 0 and
                not message_text[message_text.find("am") - 1].isspace()):
            message_text = message_text.replace("am", " am")
        if (message_text.find("AM") > 0 and
                not message_text[message_text.find("AM") - 1].isspace()):
            message_text = message_text.replace("AM", " am")
        if (message_text.find("pm") > 0 and
                not message_text[message_text.find("pm") - 1].isspace()):
            message_text = message_text.replace("pm", " pm")
        if (message_text.find("PM") > 0 and
                not message_text[message_text.find("PM") - 1].isspace()):
            message_text = message_text.replace("PM", " pm")

        doc = self.nlp_engine.process(message_text)

        dte = self.get_matches_from_multiple(
            doc, MultiTokenDictionary[st_type.lower() + '_date']
        )

        if dte:
            date_time = self.get_date_from_text(str(dte[2:]), st_type)
            if date_time and type(date_time) is not int:
                if st_type == "DEP":
                    self.declare(Fact(departure_date=date_time))
                    tags += (
                        "{DTM:" + date_time.strftime("%d %b %y @ %H_%M") + "}"
                    )
                    self.progress = self.progress.replace("dt_", "")
                elif st_type == "RET":
                    self.declare(Fact(return_date=date_time))
                    tags += (
                        "{RTM:" + date_time.strftime("%d %b %y @ %H_%M") + "}"
                    )
                    self.progress = self.progress.replace("rt_", "")
                elif st_type == "DLY":
                    self.declare(
                        Fact(departure_date=date_time.strftime("%H:%M"))
                    )
                    tags += ("{DLY:" + date_time.strftime("%H_%M") + "}")
                    self.progress = self.progress.replace("dt_", "")
            else:
                if st_type == "DEP" or st_type == "DLY":
                    request_tag = "{REQ:DDT}"
                    question_form = "departing"
                else:
                    request_tag = "{REQ:RTD}"
                    question_form = "returning"
                if st_type == "DLY":
                    type_req = "time"
                else:
                    type_req = "date and time"

                msg = "{}Sorry, I didn't quite get that. What {} are you {}?"
                if date_time:
                    if date_time == 1:
                        msg = ("{}Sorry, the return time must be after the "
                               "departure time. What {} are you {}?")
                    elif date_time == 2:
                        msg = ("{}Sorry, the time must be in the future. What "
                               "{} are you {}?")
                self.add_to_message_chain(msg.format(request_tag, type_req,
                                                     question_form))
                extra_info_appropriate = False

        return tags, extra_info_appropriate

    @DefFacts()
    def _initial_action(self):
        if len(self.message) == 0:
            self.message = [self.def_message]
        for key, value in self.knowledge.items():
            this_fact = {key: value}
            yield Fact(**this_fact)
        if "action" not in self.knowledge.keys():
            yield Fact(action="chat")
        if "complete" not in self.knowledge.keys():
            yield Fact(complete=False)
        yield Fact(extra_info_req=False)

    @Rule(AS.f1 << Fact(action="chat"),
          Fact(message_text=MATCH.message_text),
          salience=100)
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
            self.progress = "dl_dt_al_rt_rs_na_nc_"
            self.modify(f1, action="book")
        else:
            matcher.add("DELAY_PATTERN", None, TokenDictionary['delay'])
            matches = matcher(doc)
            if len(matches) > 0:
                # likely to be a delay prediction
                self.add_to_message_chain("Using the latest train data, I can "
                                          "predict how long you'll be delayed."
                                          " <br><i>Only available from Norwich to "
                                          "London Liverpool Street and "
                                          "intermediate stations.</i>",
                                          req_response=False)
                self.progress = "dl_al_dt_dd_"
                self.modify(f1, action="delay")

    # BOOKING ACTIONS
    @Rule(Fact(action="book"),
          AS.f1 << Fact(complete=False),
          AS.f2 << Fact(extra_info_req=False),
          Fact(message_text=MATCH.message_text),
          salience=99)
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
        tags = ""
        extra_info_appropriate = True

        for st_type in ["DEP", "ARR"]:
            tags, extra_info_appropriate = self.get_dep_arr_station(
                doc, message_text, tags, st_type, extra_info_appropriate
            )

        tags, extra_info_appropriate = self.get_if_return(
            doc, message_text, tags, extra_info_appropriate
        )

        for st_type in ["DEP", "RET"]:
            tags, extra_info_appropriate = self.get_dep_arr_date(
                message_text, tags, st_type, extra_info_appropriate
            )

        if "{TAG:ADT}" in message_text:
            adults_msg = message_text.replace("{TAG:ADT}", "")
            adults_doc = self.nlp_engine.process(adults_msg)
            adults = str(self.get_matches(adults_doc,
                                          TokenDictionary['dep_delay']))
            self.declare(Fact(no_adults=int(adults)))
            self.progress = self.progress.replace("na_", "")
            tags += "{ADT:" + adults + "}"
        else:
            adults = self.get_matches(doc, TokenDictionary['num_adults'])
            if adults:
                adults = str(adults[0])
                self.declare(Fact(no_adults=int(adults)))
                self.progress = self.progress.replace("na_", "")
                tags += "{ADT:" + adults + "}"

        if "{TAG:CHD}" in message_text:
            children_msg = message_text.replace("{TAG:CHD}", "")
            children_doc = self.nlp_engine.process(children_msg)
            children = str(self.get_matches(children_doc,
                                            TokenDictionary['dep_delay']))
            self.declare(Fact(no_children=int(children)))
            self.progress = self.progress.replace("nc_", "")
            tags += "{CHD:" + children + "}"
        else:
            children = self.get_matches(doc, TokenDictionary['num_children'])
            if children:
                children = str(children[0])
                self.declare(Fact(no_children=int(children)))
                self.progress = self.progress.replace("nc_", "")
                tags += "{CHD:" + children + "}"

        self.add_to_message_chain(tags, priority=7)

        if len(self.progress) != 0 and extra_info_appropriate:
            self.modify(f2, extra_info_req=True)
        elif len(self.progress) == 0:
            self.modify(f1, complete=True)

    # # Request Extra Info # #
    @Rule(Fact(action="book"),
          Fact(extra_info_req=True),
          NOT(Fact(extra_info_requested=True)),
          NOT(Fact(depart=W())),
          salience=98)
    def ask_for_departure(self):
        """Decides if need to ask user for the departure point"""
        self.add_to_message_chain("{REQ:DEP}And where are you travelling from?",
                                  1)
        self.declare(Fact(extra_info_requested=True))

    @Rule(Fact(action="book"),
          Fact(extra_info_req=True),
          NOT(Fact(extra_info_requested=True)),
          NOT(Fact(departure_date=W())),
          salience=97)
    def ask_for_departure_date(self):
        """Decides if need to ask user for the arrival point"""
        self.add_to_message_chain("{REQ:DDT}When do you want to depart?", 1)
        self.declare(Fact(extra_info_requested=True))

    @Rule(Fact(action="book"),
          Fact(extra_info_req=True),
          NOT(Fact(extra_info_requested=True)),
          NOT(Fact(arrive=W())),
          salience=96)
    def ask_for_arrival(self):
        """Decides if need to ask user for the arrival point"""
        self.add_to_message_chain("{REQ:ARR}And where are you travelling to?",
                                  1)
        self.declare(Fact(extra_info_requested=True))

    @Rule(Fact(action="book"),
          Fact(extra_info_req=True),
          NOT(Fact(extra_info_requested=True)),
          NOT(Fact(returning=W())),
          salience=95)
    def ask_for_return(self):
        """Decides if need to ask user whether they're returning"""
        self.add_to_message_chain("{REQ:RET}Are you returning?", 1,
                                  suggestions=["{TAG:RET}👍", "{TAG:RET}👎"])
        self.declare(Fact(extra_info_requested=True))

    @Rule(Fact(action="book"),
          Fact(extra_info_req=True),
          Fact(returning=True),
          NOT(Fact(extra_info_requested=True)),
          NOT(Fact(return_date=W())),
          salience=94)
    def ask_for_return_date(self):
        """Decides if need to ask user whether they're returning"""
        self.add_to_message_chain("{REQ:RTD}And when are you returning?", 1)
        self.declare(Fact(extra_info_requested=True))

    @Rule(AS.adults << Fact(no_adults=0),
          AS.children << Fact(no_children=0),
          AS.complete << Fact(complete=True),
          Fact(action="book"),
          salience=93)
    def validate_passengers_not_zero(self, adults, children, complete):
        self.add_to_message_chain("There must be at least one passenger",
                                  req_response=False)
        self.progress += "na_nc_"
        self.retract(children)
        self.retract(adults)
        self.modify(complete, complete=False)

    @Rule(Fact(action="book"),
          Fact(extra_info_req=True),
          NOT(Fact(extra_info_requested=True)),
          NOT(Fact(no_adults=W())),
          salience=92)
    def ask_for_no_adults(self):
        """Decides if need to ask user for number of adults"""
        self.add_to_message_chain("{REQ:ADT}How many adults (16+) will be "
                                  "travelling?", 1,
                                  suggestions=["{TAG:ADT}0", "{TAG:ADT}1",
                                               "{TAG:ADT}2", "{TAG:ADT}3",
                                               "{TAG:ADT}4", "{TAG:ADT}5",
                                               "{TAG:ADT}6", "{TAG:ADT}7",
                                               "{TAG:ADT}8", "{TAG:ADT}9"])
        self.declare(Fact(extra_info_requested=True))

    @Rule(Fact(action="book"),
          Fact(extra_info_req=True),
          NOT(Fact(extra_info_requested=True)),
          NOT(Fact(no_children=W())),
          salience=91)
    def ask_for_no_children(self):
        """Decides if need to ask user for number of children"""
        self.add_to_message_chain("{REQ:CHD}How many children (under 16) will "
                                  "be travelling?", 1,
                                  suggestions=["{TAG:CHD}0", "{TAG:CHD}1",
                                               "{TAG:CHD}2", "{TAG:CHD}3",
                                               "{TAG:CHD}4", "{TAG:CHD}5",
                                               "{TAG:CHD}6", "{TAG:CHD}7",
                                               "{TAG:CHD}8", "{TAG:CHD}9"])
        self.declare(Fact(extra_info_requested=True))

    @Rule(Fact(action="book"),
          Fact(complete=True),
          NOT(Fact(final_message_sent=True)),
          salience=89)
    def generate_message(self):
        self.add_to_message_chain(
            "{COMP:True}Great! I've got all I need to search for the best "
            "fare. This may take up to 20 seconds. To start the search, check "
            "details below look correct and press Start search, if something "
            "isn't quite right please click to start a new chat.<br/>",
            suggestions=["Start search &#x1F50D;",
                         "{RELOAD}Not quite right &#8635;"]
        )

        self.declare(Fact(final_message_sent=True))
        for f in self.facts:
            for g, val in self.facts[f].items():
                if g not in ["__factid__", "message_text", "extra_info_req",
                             "extra_info_requested"]:
                    self.knowledge[g] = val
        self.halt()

    @Rule(Fact(action="book"),
          Fact(final_message_sent=True),
          salience=90)
    def generate_ticket(self):

        journey_data = {}
        for f in self.facts:
            for f_id, val in self.facts[f].items():
                journey_data[f_id] = val
        try:
            if journey_data['returning']:
                ticket_type = "return"
            else:
                ticket_type = "single"

            url, ticket_data = scraper_1.scrape(journey_data)

            msg = ("The best fare for a {} ticket "
                   "between {} and {} is {}").format(
                ticket_type,
                ticket_data[1],
                ticket_data[2],
                ticket_data[0]
            )
            msg_booking = ("I have set up your booking with our preferred "
                           "booking partner Chiltern Railways by Arriva! "
                           "Click below to go through to their site to confirm "
                           "your information and complete your booking.")
            msg_final = ("Thanks for using AKOBot today! If I can be of "
                         "anymore assistance, click the button below to start "
                         "a new chat")
            self.add_to_message_chain(msg, 1, req_response=False)
            self.add_to_message_chain(msg_booking,
                                      suggestions=[
                                          "{BOOK:" + url + "}Book now &raquo;",
                                          "Start a new chat"
                                      ])
            self.add_to_message_chain(msg_final,
                                      suggestions=["Start a new chat"])
        except Exception:
            msg = ("Sorry, there are no available tickets between these "
                   "stations at this time. I'd be happy to try again for you "
                   "with a different combination of stations or times.")
            self.add_to_message_chain(msg, 1, suggestions=["Start a new chat"])

    # DELAY ACTIONS
    @Rule(Fact(action="delay"),
          AS.f1 << Fact(complete=False),
          AS.f2 << Fact(extra_info_req=False),
          Fact(message_text=MATCH.message_text),
          salience=99)
    def delay_not_complete(self, f1, f2, message_text):
        """
        If delay prediction model doesn't have enough information to be called,
        check if any more information has been provided.
                
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
        tags = ""
        extra_info_appropriate = True

        if len(self.progress) == 0:
            self.modify(f1, complete=True)
            self.progress = "ENGINE"

        for st_type in ["DEP", "ARR"]:
            tags, extra_info_appropriate = self.get_dep_arr_station(
                doc, message_text, tags, st_type, extra_info_appropriate, 1
            )

        for st_type in ["DLY"]:
            tags, extra_info_appropriate = self.get_dep_arr_date(
                message_text, tags, st_type, extra_info_appropriate
            )

        if "{TAG:DDL}" in message_text:
            dep_delay = message_text.replace("{TAG:DDL}", "")
            dep_delay_doc = self.nlp_engine.process(dep_delay)
            dep_delay_doc = str(self.get_matches(dep_delay_doc, TokenDictionary['dep_delay']))
            self.declare(Fact(departure_delay = int(dep_delay_doc)))
            self.progress = self.progress.replace("dd_", "")
            tags += "{DDL:" + str(dep_delay_doc) + "}"

        self.add_to_message_chain(tags, priority=7)

        if len(self.progress) != 0 and extra_info_appropriate:
            self.modify(f2, extra_info_req=True)
        elif len(self.progress) == 0:
            self.add_to_message_chain("Great! I can now predict when you'll "
                                      "arrive. Shouldn't take longer than 5 seconds."
                                      " Please hold on...")

    @Rule(Fact(action="delay"),
          Fact(extra_info_req=True),
          NOT(Fact(extra_info_requested=True)),
          NOT(Fact(depart=W())),
          salience=98)
    def departure_delay(self):
        """Decides if need to ask user for the departure point"""
        self.add_to_message_chain("{REQ:DEP}Where are you travelling from?",
                                  1)
        self.declare(Fact(extra_info_requested=True))

    @Rule(Fact(action="delay"),
          Fact(extra_info_req=True),
          NOT(Fact(extra_info_requested=True)),
          NOT(Fact(arrive=W())),
          salience=97)
    def arrival_delay(self):
        """Decides if need to ask user for the arrival point"""
        self.add_to_message_chain("{REQ:ARR}Where are you travelling to?",
                                  1)
        self.declare(Fact(extra_info_requested=True))

    @Rule(Fact(action="delay"),
          Fact(extra_info_req=True),
          NOT(Fact(extra_info_requested=True)),
          NOT(Fact(departure_date=W())),
          salience=96)
    def departure_time(self):
        """Decides if need to ask user for the arrival point"""
        self.add_to_message_chain("{REQ:DDT}What time were you expecting "
                                  "to depart the station?",
                                  1)
        self.declare(Fact(extra_info_requested=True))

    @Rule(Fact(action="delay"),
          Fact(extra_info_req=True),
          NOT(Fact(extra_info_requested=True)),
          NOT(Fact(departure_delay=W())),
          NOT(Fact(delay_time_received=True)),
          salience=95)
    def delay_time(self):
        self.add_to_message_chain("{REQ:DDL}How long are you delayed?",
                                  1)
        self.declare(Fact(extra_info_requested=True))
        self.declare(Fact(delay_time_received=True))

    @Rule(Fact(action="delay"),
          Fact(complete=True),
          salience=94)
    def predict_delay(self):
        journey_data = {}
        for f in self.facts:
            for f_id, val in self.facts[f].items():
                journey_data[f_id] = val
        pr = Predictions()
        try:
            delay_prediction = pr.display_results(
                journey_data['depart'], journey_data['arrive'],
                journey_data['departure_date'], journey_data['departure_delay'])
        except Exception as e:
            delay_prediction = e
        msg_final = ("Thanks for using AKOBot today! If I can be of "
                     "anymore assistance, click the button below to start "
                     "a new chat")
        self.add_to_message_chain(delay_prediction, priority=0,
                                  req_response=False)
        self.add_to_message_chain(msg_final, suggestions=["Start a new chat"])
        self.declare(Fact(can_produce_ending=True))
