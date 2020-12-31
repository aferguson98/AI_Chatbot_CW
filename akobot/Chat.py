"""
Chat.py
"""
import time
from datetime import datetime

from experta import *
from spacy.matcher import Matcher

from akobot import StationNoMatchError, StationNotFoundError
from akobot.Reasoner import ChatEngine


class Chat:
    def __init__(self):
        self.chat_log = []
        self.chat_engine = ChatEngine()

    def add_message(self, author, message_text, timestamp):
        self.chat_log.append({
            "author": author,
            "message_text": message_text,
            "time": timestamp
        })

        self.chat_engine.reset()
        self.chat_engine.declare(Fact(message_text=message_text))
        self.chat_engine.run()
        print(self.chat_engine.facts)

        return [self.chat_engine.message, self.chat_engine.suggestions]
