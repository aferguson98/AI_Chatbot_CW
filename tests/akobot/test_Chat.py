import unittest

from Chat import Booking
from akobot import StationNoMatchError, StationNotFoundError

test_case_departure = "LST"


class TestBooking(unittest.TestCase):
    def test_add_departure_from_code(self):
        booking = Booking()
        booking.add_departure("LST")
        self.assertEqual(booking.departure, test_case_departure)

    def test_add_departure_from_exact_name(self):
        booking = Booking()
        booking.add_departure("London Liverpool Street")
        self.assertEqual(booking.departure, test_case_departure)

    def test_add_departure_from_case_insensitive_name(self):
        booking = Booking()
        booking.add_departure("london Liverpool street")
        self.assertEqual(booking.departure, test_case_departure)

    def test_add_departure_from_non_exact_name(self):
        booking = Booking()
        with self.assertRaises(StationNoMatchError):
            booking.add_departure("London")

    def test_add_departure_no_station_exception(self):
        booking = Booking()
        with self.assertRaises(StationNotFoundError):
            booking.add_departure("nbakjhj2oiuaektjklanjkjah782")


if __name__ == '__main__':
    unittest.main()
