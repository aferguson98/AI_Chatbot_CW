import unittest

from experta import Fact

from akobot.Chat import Chat

test_case_departure = "ZLS"


class TestBooking(unittest.TestCase):
    def test_add_departure_from_code(self):
        booking = Chat()
        booking.chat_engine.reset()
        booking.chat_engine.declare(Fact(action="book"))
        booking.chat_engine.declare(Fact(message_text="depart from ZLS"))
        booking.chat_engine.run()
        self.assertEqual(booking.chat_engine.knowledge['depart'],
                         test_case_departure)

    def test_add_departure_from_exact_name(self):
        booking = Chat()
        booking.chat_engine.reset()
        booking.chat_engine.declare(Fact(action="book"))
        booking.chat_engine.declare(Fact(message_text="depart from London "
                                                      "Liverpool Street"))
        booking.chat_engine.run()
        self.assertEqual(booking.chat_engine.knowledge['depart'],
                         test_case_departure)

    def test_add_departure_from_case_insensitive_name(self):
        booking = Chat()
        booking.chat_engine.reset()
        booking.chat_engine.declare(Fact(action="book"))
        booking.chat_engine.declare(Fact(message_text="depart from london "
                                                      "liverpool street"))
        booking.chat_engine.run()
        self.assertEqual(booking.chat_engine.knowledge['depart'],
                         test_case_departure)

    def test_add_departure_from_non_exact_name(self):
        booking = Chat()
        booking.chat_engine.reset()
        booking.chat_engine.declare(Fact(action="book"))
        booking.chat_engine.declare(Fact(message_text="depart from London"))
        booking.chat_engine.run()
        self.assertEqual(booking.chat_engine.message[0]['message'],
                         "I found a few departure stations that matched London."
                         " Is one of these correct?")


if __name__ == '__main__':
    unittest.main()
