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

        if author != "bot":
            self.chat_engine.reset()
            self.chat_engine.declare(Fact(message_text=message_text))
            self.chat_engine.run()
            message_dict = self.chat_engine.message.pop(0)
            return [message_dict['message'],
                    message_dict['suggestions'],
                    message_dict['response_req']]

    def pop_message(self):
        message_dict = self.chat_engine.message.pop(0)
        return [message_dict['message'],
                message_dict['suggestions'],
                message_dict['response_req']]
