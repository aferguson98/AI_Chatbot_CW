"""
Chat.py
"""

from experta import *

from akobot.Reasoner import ChatEngine


def convert_tags_to_nlp_text(message):
    left_curly_braces = message.count("{")
    right_curly_braces = message.count("}")
    if left_curly_braces + right_curly_braces > 2:
        # this control sequence needs to be passed directly to nlp
        return message
    # need to replace tag with text to be useful for nlp
    message = message.replace("{FROM}", "from")
    message = message.replace("{TO}", "to")
    message = message.replace("{TAG:DAT}", "departing at")
    message = message.replace("{TAG:RAT}", "returning at")
    return message


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
            message_text = convert_tags_to_nlp_text(message_text)
            self.chat_engine.reset()
            self.chat_engine.declare(Fact(message_text=message_text))
            self.chat_engine.run()
            message_dict = self.chat_engine.message.pop(0)
            tags = self.chat_engine.tags
            self.chat_engine.tags = ""
            print(self.chat_engine.facts)
            return [tags + message_dict['message'],
                    message_dict['suggestions'],
                    message_dict['response_req']]

    def pop_message(self):
        if len(self.chat_engine.message) > 0:
            message_dict = self.chat_engine.message.pop(0)
        else:
            message_dict = {
                'message': "Sorry! Something has gone wrong with this chat. "
                           "Please reload the page",
                'suggestions': ["Reload Page"],
                'response_req': True
            }
        tags = self.chat_engine.tags
        self.chat_engine.tags = ""
        return [tags + message_dict['message'],
                message_dict['suggestions'],
                message_dict['response_req']]
