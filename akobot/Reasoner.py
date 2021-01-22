"""
Reasoner.py

Contains classes related to reasoning
"""
from difflib import SequenceMatcher

from dateparser.date import DateDataParser
from experta import *
from spacy.matcher import Matcher

from Database.DatabaseConnector import DBConnection
from akobot import StationNoMatchError, StationNotFoundError, \
    UnknownPriorityException, UnknownStationTypeException, scraper_1
from akobot.AKOBot import NLPEngine

TokenDictionary = {
    "book": [{"LEMMA": {"IN": ["book", "booking", "purchase", "buy"]}}],
    "delay": [{"LEMMA": {"IN": ["delay", "predict", "prediction"]}}],
    "help": [{"LEMMA": {"IN": ["help", "support", "assistance"]}}],
    "yes": [{"LOWER": {"IN": ["yes", "yeah", "y", "yep", "yeh", "ye", "👍"]}}],
    "no": [{"LOWER": {"IN": ["no", "nope", "n", "nah", "na", "👎"]}}],
    "depart": [{"POS": "ADP", "LEMMA": {"IN": ["depart", "from", "departing"]}},
               {"POS": "PROPN", "OP": "*"}, {"POS": "PROPN", "DEP": "pobj"}],
    "arrive": [{"POS": "ADP", "LEMMA": {"IN": ["arrive", "to", "arriving"]}},
               {"POS": "PROPN", "OP": "*"}, {"POS": "PROPN", "DEP": "pobj"}],
    "return": [{"LEMMA": {"IN": ["return", "returning"]}}],
    "single": [{"LEMMA": {"IN": ["single", "one-way"]}}],
    "dep_date": [{"LEMMA": {"IN": ["depart", "departing", "leave", "leaving"]}},
                 {"POS": "ADP"}, {"ENT_TYPE": "DATE", "OP": "+"},
                 {"POS": "ADP", "OP": "?"}, {"SHAPE": "dd:dd"}],
    "other_dep_date": [{"LEMMA": {"IN": ["depart", "departing", "leave", "leaving"]}},
                    {"POS": "ADP"}, {"ENT_TYPE": "TIME", "OP": "+"},
                    {"POS": "ADP", "OP": "?"},{"ENT_TYPE": "TIME", "OP": "?"}],
                    # add another ent_type : DATE without OP : +
    "ret_date": [{"LEMMA": {"IN": ["return", "returning"]}},
                 {"POS": "ADP"}, {"ENT_TYPE": "DATE", "OP": "*"},
                 {"POS": "ADP", "OP": "?"}, {"ENT_TYPE": "TIME", "OP": "*"},
                 {"ENT_TYPE": "TIME", "DEP": "pobj"}]
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


def get_date_from_text(date_text):
    date_text = date_text.replace(" am", "am")
    date_text = date_text.replace(" AM", "am")
    date_text = date_text.replace(" pm", "pm")
    date_text = date_text.replace(" PM", "pm")
    print("DATE>>>>", date_text)
    ddp = DateDataParser(languages=['en'])
    return ddp.get_date_data(date_text).date_obj


class ChatEngine(KnowledgeEngine):
    def __init__(self):
        super().__init__()

        # Internal connections to AKOBot classes
        self.db_connection = DBConnection('AKODatabase.db')
        self.nlp_engine = NLPEngine()

        # Knowledge dict
        self.knowledge = {}
        self.booking_progress = "dl_dt_al_rt_rs_na_nc_"

        # User Interface output
        self.def_message = {"message": "I'm sorry. I don't know how to help "
                                       "with that just yet. Please try again",
                            "suggestions": [],
                            "response_req": True}
        self.message = []
        self.tags = ""

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

    def get_dep_arr_station(self, doc, message_text, tags, st_type,
                            extra_info_appropriate=True):
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
        elif st_type == "ARR":
            # Arrival Station
            found_mul_msg = ("I found a few arrival stations that matched {}."
                             " Is one of these correct?")
            found_none_msg = ("I couldn't find any arrival stations matching {}"
                              ". Please try again.")
            progress_tag = "al_"
            token = "arrive"
        else:
            raise UnknownStationTypeException(st_type)

        search_station = None
        matches = self.get_matches(doc, TokenDictionary[token])
        if matches is not None:
            search_station = str(matches[1:])
        elif "{TAG:" + st_type + "}" in message_text:
            search_station = message_text.replace("{TAG:" + st_type + "}", "")
        elif "arriving to" in message_text and st_type=="ARR":
            search_station = message_text.split("arriving to")[1]

        if search_station:
            try:
                station = self.find_station(search_station)
                tags += "{" + st_type + ":" + station[1] + "}"
                if st_type == "DEP":
                    self.declare(Fact(depart=station[0]))
                else:
                    self.declare(Fact(arrive=station[0]))
                self.booking_progress = self.booking_progress.replace(progress_tag, "")
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
            print("User wants to return ????????", ret)
            if ret is None:
                ret = self.get_matches(doc, TokenDictionary['return'])
            print("RETURN YES", ret)
            sgl = self.get_matches(doc, TokenDictionary['no'])
            print("USER WANT SINGLE??????", sgl)
            if sgl is None:
                sgl = self.get_matches(doc, TokenDictionary['single'])
            print("SINGLE YES", sgl)
        else:
            ret = self.get_matches(doc, TokenDictionary['return'])
            sgl = self.get_matches(doc, TokenDictionary['single'])
        if ret is not None and sgl is None:
            tags += "{RET:RETURN}"
            self.declare(Fact(returning="True"))
            self.booking_progress = self.booking_progress.replace("rs_", "")
        elif sgl is not None and ret is None:
            tags += "{RET:SINGLE}{RTM:N/A}"
            self.declare(Fact(returning="False"))
            self.booking_progress = self.booking_progress.replace("rs_", "")
            self.booking_progress = self.booking_progress.replace("rt_", "")
        elif sgl is not None and ret is not None:
            self.add_to_message_chain("{REQ:RET}Sorry, I don't understand. "
                                      "Are you returning? Try answering YES or "
                                      "NO.", 0, suggestions=["{TAG:RET} Yes",
                                                             "{TAG:RET} No"])
            extra_info_appropriate = False
        return tags, extra_info_appropriate

    def get_dep_arr_date(self, doc, message_text, tags, st_type="DEP"):
        print(doc)
        for d in doc:
            print(d)
            print(d.ent_type_)
        if st_type == "DEP":
            dte = self.get_matches(doc, TokenDictionary['dep_date'])
            print("DTEEEEEE==========", dte)
            if dte is None: 
                dte = self.get_matches(doc, TokenDictionary['other_dep_date'])
                print("<<<<<TRYING TO GET DTEEEEE", dte)
        elif st_type == "RET":
            dte = self.get_matches(doc, TokenDictionary['ret_date'])
            print(dte)  
        else:
            raise UnknownStationTypeException(st_type)

        if dte is not None:
            date_time = get_date_from_text(str(dte[2:]))
            if st_type == "DEP":
                
                self.declare(Fact(departure_date=date_time))
                tags += "{DTM:" + date_time.strftime("%d %b %y @ %H_%M") + "}"
                self.booking_progress = self.booking_progress.replace("dt_", "")
            else:

                self.declare(Fact(return_date=date_time))
                tags += "{RTM:" + date_time.strftime("%d %b %y @ %H_%M") + "}"
                self.booking_progress = self.booking_progress.replace("rt_", "")
        return tags

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
            self.modify(f1, action="book")
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

        print(len(self.booking_progress), self.booking_progress)

        for st_type in ["DEP", "ARR"]:
            tags, extra_info_appropriate = self.get_dep_arr_station(
                doc, message_text, tags, st_type, extra_info_appropriate
            )

        tags, extra_info_appropriate = self.get_if_return(
            doc, message_text, tags, extra_info_appropriate
        )

        for st_type in ["DEP", "RET"]:
            tags = self.get_dep_arr_date(
                doc, message_text, tags, st_type
            )

        if "{TAG:ADT}" in message_text:
            adults = message_text.replace("{TAG:ADT}", "")
            self.declare(Fact(no_adults=adults))
            tags += "{ADT:" + adults + "}"
            self.booking_progress = self.booking_progress.replace("na_", "")

        if "{TAG:CHD}" in message_text:
            children = message_text.replace("{TAG:CHD}", "")
            self.declare(Fact(no_children=children))
            tags += "{CHD:" + children + "}"
            self.booking_progress = self.booking_progress.replace("nc_", "")

        self.add_to_message_chain(tags, priority=7)

        print(len(self.booking_progress), self.booking_progress)

        if len(self.booking_progress) != 0 and extra_info_appropriate:
            self.modify(f2, extra_info_req=True)
        elif len(self.booking_progress) == 0:
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
        self.add_to_message_chain("{REQ:DDT}When do you want to depart? (Date AT time)",
                                  1)
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

    @Rule(Fact(action="book"),
          Fact(extra_info_req=True),
          NOT(Fact(extra_info_requested=True)),
          NOT(Fact(no_adults=W())),
          salience=93)
    def ask_for_no_adults(self):
        """Decides if need to ask user for number of adults"""
        self.add_to_message_chain("{REQ:ADT}How many adults (16+) will be "
                                  "travelling?", 1,
                                  suggestions=["{TAG:ADT}1", "{TAG:ADT}2",
                                               "{TAG:ADT}3", "{TAG:ADT}4",
                                               "{TAG:ADT}5", "{TAG:ADT}6",
                                               "{TAG:ADT}7", "{TAG:ADT}8",
                                               "{TAG:ADT}9", "{TAG:ADT}10"])
        self.declare(Fact(extra_info_requested=True))

    @Rule(Fact(action="book"),
          Fact(extra_info_req=True),
          NOT(Fact(extra_info_requested=True)),
          NOT(Fact(no_children=W())),
          salience=92)
    def ask_for_no_children(self):
        """Decides if need to ask user for number of children"""
        self.add_to_message_chain("{REQ:CHD}How many children (under 16) will "
                                  "be travelling?", 1,
                                  suggestions=["{TAG:CHD}1", "{TAG:CHD}2",
                                               "{TAG:CHD}3", "{TAG:CHD}4",
                                               "{TAG:CHD}5", "{TAG:CHD}6",
                                               "{TAG:CHD}7", "{TAG:CHD}8",
                                               "{TAG:CHD}9", "{TAG:CHD}10"])
        self.declare(Fact(extra_info_requested=True))

    @Rule(Fact(action="book"),
          Fact(complete=True),
          salience=91)
    def generate_ticket(self):
        journey_data = {}
        for f in self.facts:
            for f_id, val in self.facts[f].items():
                journey_data[f_id] = val
        try:
            url, json = scraper_1.scrape(journey_data)
            print(url)
            if journey_data['returning']:
                ticket_price = json['returnJsonFareBreakdowns']
                print(len(ticket_price))
                if len(ticket_price) == 0:
                    ticket_price = json['singleJsonFareBreakdowns'][0]
                    ticket_price = float(ticket_price['ticketPrice']) * 2
                else:
                    ticket_price = ticket_price[0]['ticketPrice']
                ticket = ["return", ticket_price]
            else:
                ticket = ["return",
                          json['singleJsonFareBreakdowns'][0]['ticketPrice']]
            msg = ("Great, I've got all I need. The best fare for a {} ticket "
                   "between {} and {} is £{:.2f}").format(
                        ticket[0],
                        json['jsonJourneyBreakdown']['departureStationName'],
                        json['jsonJourneyBreakdown']['arrivalStationName'],
                        ticket[1]
                   )
            msg_booking = ("I have set up your booking with our preferred "
                           "booking partner Chiltern Railways by Arriva! "
                           "Click below to go through to their site to confirm "
                           "your information and complete your booking.")
            self.add_to_message_chain(msg, 1, req_response=False)
            self.add_to_message_chain(msg_booking, 1,
                                      suggestions=[{"BOOK:" + url}])
        except StationNotFoundError as e:
            print("ERROR:", e)
            msg = ("Sorry, there are no available tickets between these "
                   "stations at this time. Please try another station "
                   "combination or time.")
            self.add_to_message_chain(msg, 1)

    # DELAY ACTIONS

    # HELP ACTIONS

    @Rule(salience=1)
    def add_all_facts_to_dict(self):
        for f in self.facts:
            for g, val in self.facts[f].items():
                if g not in ["__factid__", "message_text", "extra_info_req",
                             "extra_info_requested"]:
                    self.knowledge[g] = val
