import sys, os
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import numpy as np
import pandas as pd
from sklearn import neighbors
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from datetime import datetime
from Database.DatabaseConnector import DBConnection
from difflib import SequenceMatcher




class Predictions:
    def __init__(self):
        self.db_connection = DBConnection('AKODatabase.db')
        self.stations = {
            "norwich": "NRCH",
            "diss": "DISS",
            "stowmarket": "STWMRKT",
            "ipswich": "IPSWICH",
            "manningtree": "MANNGTR",
            "colchester": "CLCHSTR",
            "witham": "WITHAME",
            "chelmsford": "CHLMSFD",
            "ingatestone": "INT",
            "shenfield": "SHENFLD",
            "stanford": "STFD",
            "stanford-le-hope": "STFD",
            "london liverpool street": "LIVST",
            "london liverpool st": "LIVST",
            "liverpool street": "LIVST"
        }
        # morning: 5 - 10, midday: 10-15, evening: 15 - 20, night: 20 - 5
        self.segment_of_day = None
        self.rush_hour = None  # (06 - 09 and 16:00-:18:00) = 1
        self.day_of_week = datetime.today().weekday()  # 0 = Mon and 6 = Sun
        self.weekend = self.is_weekend(
            self.day_of_week)  # Monday - Friday = 1; Saturday and Sunday = 0
        self.departure_station = None
        self.arrival_station = None
        self.exp_dep = None
        self.delay = None

    def station_finder(self, station):
        """
        Function to find the corresponding station abbreviation based on the
        provided station from user

        Parameters
        ----------
        station: string 
            Station name - i.e. Ipswich

        Returns
        -------
        string:
            Abbreviation of the station provided
        """

        print("Received station>>62>>",station)
        x = station.lower()

        similar = ''
        if x in self.stations:
            return self.stations[x]
        else:
            for s in (self.stations):
                ratio = SequenceMatcher(None, x, s).ratio() * 100
                if ratio >= 60:  # Need to check what value is acceptable
                    similar = s
                    print()
                    print("The city you've provided has not been found. "
                          "Closest match to " + station + "  is: " + s.upper())  
            if similar == '':
                raise Exception(("No similar cities to " + station + " have been found. "
                      "Please type again the station"))

            return similar

    def harvest_data(self):
        """
        Pulls all journeys from DB that have FROM and TO station and don't have
        null values as arrival/departure times
        """
        # main.March2019Data - contains 2019 March Data
        # main.TrainingData - contains all CSV data
        # main.TransformedTraining - Contains data with no NULLS
        # main.Data - contains no NULL data from 2018 and 2019
        query = """
            SELECT rid_FROM, tpl_FROM, ptd, dep_at, tpl_TO, pta, arr_at FROM
                (SELECT rid AS rid_FROM, tpl AS tpl_FROM, ptd, dep_at 
                 FROM main.Data WHERE tpl = '{0}') AS x JOIN
                (SELECT rid AS rid_TO, tpl AS tpl_TO, pta, arr_at FROM main.Data 
                 WHERE tpl = '{1}') AS y on x.rid_FROM = y.rid_TO 
                ORDER BY rid_FROM """.format(self.departure_station,
                                             self.arrival_station)

        result = self.db_connection.send_query(query).fetchall()
        return result

    @staticmethod
    def convert_time(time):
        """
        Convert given time (in seconds) to hours, minutes, seconds
        """
        tt = []
        hh = int(time[0][0] / 3600)
        tt.append(hh)
        time[0][0] = time[0][0] - (hh * 3600)
        mm = int(time[0][0] / 60)
        tt.append(mm)
        time[0][0] = time[0][0] - (mm * 60)
        ss = int(time[0][0] % 60)
        tt.append(ss)

        return tt

    @staticmethod
    def is_weekend(day):
        """
        Checks if the day of the week is weekday or weekend

        Parameters
        ---------
            day - int
                day of the week 0 = Monday, 6 = Sundau

        Returns
        -------
            weekday = list
                One hot encoding for weekday(0) or weekend(1)
        """
        weekend = None
        if day <= 4:
            weekend = 0
        elif 4 < day < 7:
            weekend = 1
        return weekend

    @staticmethod
    def check_day_segment(hour_of_day):
        """
            Checks if it's morning/midday/evening/night given hour of day

        Parameters
        -----------
            hourOfDay - int

        Returns
        -------
            segmentOfDay - list
                One hot encoding for morning/midday/evening/night
        """
        segment_of_day = None
        if 5 <= hour_of_day < 10:
            segment_of_day = 1
        elif 10 <= hour_of_day < 15:
            segment_of_day = 2
        elif 15 <= hour_of_day < 20:
            segment_of_day = 3
        elif (20 <= hour_of_day < 24) or (0 <= hour_of_day < 5):
            segment_of_day = 4
        return segment_of_day

    @staticmethod
    def is_rush_hour(hour, minute):
        """
            Checks if it's rush hour or not based on the time given

        Parameters
        ----------
            hour - int
                hour of day 
            minute - int
                minute of day
        Returns
        -------
            rushHour - list
                One hot encoding if rush hour(1) or not(0)
        """
        rush_hour = []

        if (5 <= hour <= 9) or (16 <= hour <= 18):
            if (hour == 5 and 45 <= minute < 60) or (5 < hour < 9):
                rush_hour = 1
            elif (hour == 5 and minute < 45) or (hour == 9 and 0 < minute):
                rush_hour = 0
            elif 16 <= hour or (hour <= 18 and minute == 0):
                rush_hour = 1
        elif (9 < hour < 16) or (hour == 9 and 0 < minute < 60) or (
                18 < hour < 24) or (0 < hour < 5):
            rush_hour = 0

        return rush_hour

    
    def prepare_datasets(self):
        """
        Queries data with FROM and TO stations and distributes values 
            used for prediction

        Returns
        -------
        data - List of all data necessary for predictions
        """
        result = self.harvest_data()
        data = []

        for journey in range(len(result)):
            #   public_departure      |       actual_departure 
            if (result[journey][2] != '' and result[journey][3] != '' and 
                    #public_arrival      |       actual_arrival
                    result[journey][5] != '' and result[journey][6] != ''):
                # Get date based on RID
                rid = str(result[journey][0])
                # Convert date to day of the week
                day_of_week = datetime(int(rid[:4]), int(rid[4:6]),
                                        int(rid[6:8])).weekday()
                hour_of_day = int(result[journey][3].split(":")[0])
                minute_of_day = int(result[journey][3].split(":")[1])
                # Get day of week based on RID - Monday = 0, Sunday = 6
                weekend = self.is_weekend(day_of_week)
                # Checking morning/midday/evening/night
                day_segment = self.check_day_segment(hour_of_day)
                # Checking rush hour or not
                rush_hour = self.is_rush_hour(hour_of_day, minute_of_day)
                try:
                    # Departing time  in seconds
                    time_dep = (datetime.strptime(result[journey][3], '%H:%M') -
                                datetime(1900, 1, 1)).total_seconds()
                except:
                    print("Unable to get time_dep")
                try:
                    # Delay : actual departure - public timetable departure in seconds
                    journey_delay = ((datetime.strptime(result[journey][3], '%H:%M') -
                                datetime(1900, 1, 1)).total_seconds() -
                                (datetime.strptime(result[journey][2], '%H:%M') -
                                datetime(1900, 1, 1)).total_seconds())
                except:
                    print("Unable to get journey_delay")
                try:
                    # Arrival : actual arrival - public timetable arrival in seonds
                    time_arr = ((datetime.strptime(result[journey][6], '%H:%M') -
                                    datetime(1900, 1, 1)).total_seconds() -
                                    (datetime.strptime(result[journey][5], '%H:%M') -
                                    datetime(1900, 1, 1)).total_seconds())
                except:
                    print("Unable to get  time_arrival")
                

                # Add all above into dataset used for prediction
                data.append([rid, time_dep, journey_delay, day_of_week, 
                            weekend, day_segment, rush_hour,  time_arr])

        return data

        
    def predict(self, data):
        """
        Predicts how long the user will be delayed using nearest neighbours
            model.
        
        Parameters
        ----------
        data - List of all data needed for predicting

        Returns
        -------
        prediction - list  of time how long the user will be delayed.
        """
        dep_time_s = (datetime.strptime(self.exp_dep, '%H:%M') - datetime(
                            1900, 1, 1)).total_seconds()
        delay_s = int(self.delay) * 60
        journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay", "day_of_week","weekend", 
                            "day_segment", "rush_hour", "arrival_time"])

        X = journeys.drop(['rid','arrival_time'], axis=1)
        y = journeys['arrival_time'].values
        
        clf = neighbors.NearestNeighbors(n_neighbors=1)
        clf.fit(X)

        prediction = clf.kneighbors([[dep_time_s, delay_s, self.day_of_week, self.weekend, 
                                            self.segment_of_day, self.rush_hour]])
        prediction = self.convert_time(prediction[0])

        print("The total delay of the journey will be " + str(prediction[1]).zfill(2) + 
                                " minutes and " + str(prediction[2]).zfill(2) + " seconds.")
        return prediction

    def display_results(self, from_st, to_st, exp_dep, delay):
        """
        Linking function of both data preparation and prediction
        Sends result to reasoning engine

        Parameters
        ----------
        from_st - String - departing station name
        to_st - String - arriving station name
        exp_dep - Datetime - when user was expecting to depart
        delay - Integer - how long user was delayed (in minutes)

        Returns
        -------
        Sentence including predicted delay to arriving station.

        """
   
        self.departure_station = self.station_finder(from_st)
        self.arrival_station = self.station_finder(to_st)
        self.exp_dep = exp_dep
        hour_of_day = int(exp_dep.split(":")[0])
        minute_of_day = int(exp_dep.split(":")[1])
        self.delay = delay
        self.segment_of_day = self.check_day_segment(hour_of_day)
        self.rush_hour = self.is_rush_hour(hour_of_day, minute_of_day)

        data = self.prepare_datasets()

        prediction = self.predict(data)

        return ("The total delay of the journey will be " + str(prediction[1]).zfill(2) + 
                                " minutes and " + str(prediction[2]).zfill(2) + " seconds.")


# pr = Predictions()
# a = pr.display_results("norwich", "diss", "7:30", "4")
# print(a)