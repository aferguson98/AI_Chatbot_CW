import sys, os
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import numpy as np
from sklearn import preprocessing, neighbors, svm
from sklearn import metrics
from sklearn.metrics import mean_squared_error, f1_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import OneHotEncoder
import pandas as pd
import csv
from datetime import datetime, timedelta
from Database.DatabaseConnector import DBConnection
from difflib import SequenceMatcher, get_close_matches

class Predictions:
    def __init__(self):
        self.departure_station = ""
        self.arrival_station = ""
        self.time_departure = ""
        self.day_of_week = datetime.today().weekday() # 0 = Monday and 6 = Sunday
        self.db_connection = DBConnection('AKODatabase.db')
        self.journeys = {}
        self.stations = {
                "norwich" : "NRCH",
                "diss" : "DISS",
                "stowmarket" : "STWMRKT",
                "ipswich" : "IPSWICH",
                "manningtree" : "MANNGTR",
                "colchester" : "CLCHSTR",
                "witham" : "WITHAME",
                "chelmsford" : "CHLMSFD",
                "ingatestone" : "INT",
                "shenfield" : "SHENFLD",
                "stanford" : "STFD",
                "liverpool st" : "LIVST"
            }
        self.segment_of_day = [] #morning: 5 - 10, midday: 10-15, evening: 15 - 20, night: 20 - 5 
        self.rush_hour = [] # (06 - 09 and 16:00-:18:00) = 1
        self.weekday = self.is_weekday(self.day_of_week) # Monday - Friday = 1; Saturday and Sunday = 0
    
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
        
        x = station.lower()
        similar = ''
        if x in self.stations:
            return self.stations[x]
        else:
            for s in (self.stations):
                ratio = SequenceMatcher(None, x, s).ratio() * 100
                if ratio >= 60: # Need to check what value is acceptable. For "DS" a response "DISS" is found with value 66.666 
                    similar = s
                    print(ratio)
                    print("The city you've provided has not been found. Closest match to " + station + "  is: " + s.upper())
            if similar == '':
                print("No similar cities to " + station + " have been found. Please type again the station")
            return similar

    def harvest_data(self):
        """
        Pulls all journeys from DB that have FROM and TO station and don't have null values as arrival/departure times
        """
        # main.March2019Data - contains 2019 March Data
        # main.TrainingData - contains all CSV data
        # main.TransformedTraining - Contains data with no NULLS
        # main.Data - contains no NULL data from 2018 and 2019
        query = """SELECT rid_FROM, tpl_FROM, ptd, dep_at, tpl_TO, pta, arr_at FROM
                            (SELECT rid AS rid_FROM, tpl AS tpl_FROM, ptd, dep_at FROM main.Data 
                            WHERE tpl = '{0}') AS x
                            JOIN
                            (SELECT rid AS rid_TO, tpl AS tpl_TO, pta, arr_at FROM main.Data 
                            WHERE tpl = '{1}') AS y 
                            on x.rid_FROM = y.rid_TO
                        ORDER BY rid_FROM """.format(self.departure_station, self.arrival_station)
   
        result = self.db_connection.send_query(query).fetchall()
        return result

    def convert_time(self, time):
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


    def is_weekday(self, day):
        """
        Checks if the day of the week is weekday or weekend

        Parameters
        ---------
            day - int
                day of the week 0 = Monday, 6 = Sundau

        Returns
        -------
            weekday = list
                One hot encoding for weekday(1) or weekend(0)
        """
        weekday = []
        if day <= 4:
            weekday = [1]
        elif 4 < day < 7:
            weekday = [0]
        return weekday


    def check_day_segment(self, hour_of_day):
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
        segment_of_day = []
        if 5 <= hour_of_day < 10:
            segment_of_day = [1, 0, 0, 0]
        elif 10 <= hour_of_day < 15:
            segment_of_day = [0, 1, 0, 0]
        elif 15 <= hour_of_day < 20:
            segment_of_day = [0, 0, 1, 0]
        elif (20 <= hour_of_day < 24) or (0 <= hour_of_day < 5):
            segment_of_day = [0, 0, 0, 1]
        return segment_of_day


    def is_rush_hour(self, hour, minute):
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

        if (5 <= hour <= 9 ) or (16 <= hour <= 18):
            if (hour == 5 and 45 <= minute < 60) or (5 < hour < 9):
                rush_hour = [1]
            elif (hour == 5 and minute < 45) or (hour == 9 and 0 < minute):
                rush_hour = [0]
            elif 16 <= hour or (hour <= 18 and minute == 0):
                rush_hour = [1]
        elif (9 < hour < 16) or (hour == 9 and 0 < minute < 60) or (18 < hour < 24) or (0 < hour < 5):
            rush_hour = [0]

        return rush_hour


    def knn(self, x_data, y_data):
        """
            K nearest neighbours prediction

            Parameters
            ----------
            x_data - array
                Data serving as input
            y_data - array
                Data serving as output

            Returns
            -------
            Predicted value based on the input - estimated time user will be delayed
        """
        
        time_depart_s = (datetime.strptime(self.time_departure, '%H:%M') - datetime(1900,1,1)).total_seconds()
        prediction_input = []
        prediction_input.append(self.day_of_week)
        prediction_input.extend(self.weekday)
        prediction_input.append(time_depart_s)
        prediction_input.extend(self.segment_of_day)
        prediction_input.extend(self.rush_hour)

        # turn the variables into numpy arrays so they can be reshaped for training the model.
        X = np.array(x_data)
        Y = np.array(y_data)
        prediction_input = np.array(time_depart_s)

        # Splitting data into 80-20 train/test
        X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size = 0.2)

        # Reshape the data into 2D arrays so it can be used to train
        X_train = X_train.reshape(-1, 1)
        y_train = y_train.reshape(-1, 1)
        X_test = X_test.reshape(-1, 1)
        y_test = y_test.reshape(-1, 1)
        prediction_input = prediction_input.reshape(-1, 1)

        # Specifying type of classification and training
        clf = neighbors.KNeighborsRegressor()
        clf.fit(X_train, y_train)

        prediction_s = clf.predict(prediction_input)

        return prediction_s


    def mlp(self, x_data, y_data):
        """
            Multi-layer perception neural network prediction

            Parameters
            ----------
            x_data - array
                Data serving as input
            y_data - array
                Data serving as output

            Returns
            -------
            Predicted value based on the input - estimated arrival time at station X
        """
        
        time_depart_s = (datetime.strptime(self.time_departure, '%H:%M') - datetime(1900,1,1)).total_seconds()
        prediction_input = []
        prediction_input.append(self.day_of_week)
        prediction_input.extend(self.weekday)
        prediction_input.append(time_depart_s)
        prediction_input.extend(self.segment_of_day)
        prediction_input.extend(self.rush_hour)

        # turn the variables into numpy arrays so they can be reshaped for training the model.
        X = np.array(x_data)
        Y = np.array(y_data)
        prediction_input = np.array(time_depart_s)

        # Splitting data into 80-20 train/test
        X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size = 0.2)

        # Reshape the data into 2D arrays so it can be used to train
        X_train = X_train.reshape(-1, 1)
        y_train = y_train.reshape(-1, 1)
        X_test = X_test.reshape(-1, 1)
        y_test = y_test.reshape(-1, 1)
        prediction_input = prediction_input.reshape(-1, 1)

        # Specifying type of classification and training
        clf = MLPRegressor(hidden_layer_sizes = (32,16,8), activation="relu", solver="adam", random_state=1, max_iter = 2000)
        clf.fit(X_train, y_train.ravel())

        prediction_s = clf.predict(prediction_input)

        return prediction_s


    def predict_arrival(self):
        """
            Predicting when the train will arrive at the TO station
        """

        X = []
        Y = []
        result = self.harvest_data()
        
        for journey in range(len(result)):
            J = []
            K = []
            
            # public_departure              actual_departure              public_arrival               actual_arrival
            if result[journey][2] != '' and result[journey][3] != '' and result[journey][5] != '' and result[journey][6] != '':
                # Get date based on RID
                date = str(result[journey][0])
                # Convert date to day of the week
                day_of_week = datetime(int(date[:4]), int(date[4:6]), int(date[6:8])).weekday()
                hour_of_day = int(result[journey][3].split(":")[0])
                minute_of_day = int(result[journey][3].split(":")[1])

                # Get day of week based on RID - Monday = 0, Sunday = 6
                weekday = self.is_weekday(day_of_week)
                
                # Checking morning/midday/evening/night
                day_segment = self.check_day_segment(hour_of_day)

                # Checking rush hour or not
                rush_hour = self.is_rush_hour(hour_of_day, minute_of_day)

                # Add day of week, weekday/end, actual departurein seconds, morning/evening, rush/norush hour to X
                try:
                    J.append(day_of_week)
                    J.extend(weekday)
                    J.append((datetime.strptime(result[journey][3], '%H:%M') - datetime(1900,1,1)).total_seconds())
                    J.extend(day_segment)
                    J.extend(rush_hour)

                    X.append(J)
                except:
                    print("Unable to convert DEPARTURE to seconds")
                # Add day of week, weekday/end, aactual arrival in seconds, morning/evening, rush/norush hour to Y
                try:
                    K.append(day_of_week)
                    K.extend(weekday)
                    K.append((datetime.strptime(result[journey][6], '%H:%M') - datetime(1900,1,1)).total_seconds())
                    K.extend(day_segment)
                    K.extend(rush_hour)

                    Y.append(K)
                except:
                    print("Unable to convert ARRIVAL to seconds")

        arrival = self.mlp(X, Y)
        arrival_time = self.convert_time([arrival])

        return arrival_time


    def predict_delay(self):
        """
            Predicting how long the train will be delayed
        """
        X = []
        Y = []
        result = self.harvest_data()

        for journey in range(len(result)):
            J = []
            K = []
            #    public_departure            actual_departure              public_arrival               actual_arrival
            if result[journey][2] != '' and result[journey][3] != '' and result[journey][5] != '' and result[journey][6] != '':
                # Get date based on RID
                date = str(result[journey][0])
                # Convert date to day of the week
                day_of_week = datetime(int(date[:4]), int(date[4:6]), int(date[6:8])).weekday()
                hour_of_day = int(result[journey][3].split(":")[0])
                minute_of_day = int(result[journey][3].split(":")[1])

                # Get day of week based on RID - Monday = 0, Sunday = 6
                weekday = self.is_weekday(day_of_week)
                
                # Checking morning/midday/evening/night
                day_segment = self.check_day_segment(hour_of_day)

                # Checking rush hour or not
                rush_hour = self.is_rush_hour(hour_of_day, minute_of_day)

                try:
                    J.append(day_of_week)
                    J.extend(weekday)
                    J.append((datetime.strptime(result[journey][3], '%H:%M') - datetime(1900,1,1)).total_seconds() - 
                            (datetime.strptime(result[journey][2], '%H:%M') - datetime(1900,1,1)).total_seconds())
                    J.extend(day_segment)
                    J.extend(rush_hour)
                    
                    X.append(J)
                except:
                    print("Unable to convert DEPARTURE to seconds")
                # Add (actual arrival - expected arrival) in seconds to Y
                try:
                    K.append(day_of_week)
                    K.extend(weekday)
                    K.append((datetime.strptime(result[journey][6], '%H:%M') - datetime(1900,1,1)).total_seconds() - 
                            (datetime.strptime(result[journey][5], '%H:%M') - datetime(1900,1,1)).total_seconds())
                    K.extend(day_segment)
                    K.extend(rush_hour)
                    
                    Y.append(K)
                except:
                    print("Unable to convert ARRIVAL to seconds")
                
        prediction_s = self.knn(X, Y)
        delayed_time = self.convert_time(prediction_s)

        return delayed_time

       
    def display_results(self, FROM, TO, Tdepart):
        """
        Collect predictions and return then to front-end


        """
        self.departure_station = self.station_finder(FROM)
        self.arrival_station = self.station_finder(TO)
        self.time_departure = Tdepart
        hour_of_day = int(Tdepart.split(":")[0])
        minute_of_day = int(Tdepart.split(":")[1])

        self.segment_of_day = self.check_day_segment(hour_of_day)

        # Check if rush hour or not
        self.rush_hour = self.is_rush_hour(hour_of_day, minute_of_day)

        arrival = self.predict_arrival()
        delay = self.predict_delay()

        if (delay[0] == 0) and (delay[1] == 0):
            return ("Your journey is expected to be delayed by less than a minute. You will arrive at " + TO +  " at " + str(arrival[0]) 
                + ":" + str(arrival[1]))
        elif delay[0] == 0:
            return ("You will arrive at " + TO +  " at " + str(arrival[0]).zfill(2) + ":" + str(arrival[1]).zfill(2) + 
                    ". The total journey delay is predicted to be " + str(delay[1]).zfill(2) + 
                    " minutes and " + str(delay[2]).zfill(2) + " seconds.")




# pr = Predictions()
# pr.station_finder("DS")
# pr.station_finder("Norwich")
# pr.display_results("Norwich", "Colchester", "17:30")



# KNN gets similar outputs, so far seems to be the closest to reality.

# Multi-Layer Processor (MLP) - 
#   3 hidden layers - 32/16/8 neurons. Activation function "identity" - produces consistent results
#   however size of inputs doesn't affect output as much. The default "Relu" is the choice - producing consistent outputs which 
#   are affected by the size of the input. 
#   Unable to use MLP for delay prediction. The output is more like time, rather than actual delay (minutes/seconds).
# 
#   Solver -  tested between "lbfgs" and "adam". Documentation suggests to use "adam" for large data sets.
#       Both "lbfgs" and "adam" have produced similar results, however same as type of activation function, 
#       "lbfgs" output doesn't get much affected by the size of the input, producing similar results for both x (size of input) == 1 or more
#       "adam" output differ by a few minutes (for size of input 1 or more), however multiple runs prove that larger input size produces
#           more consistent results with little difference between each other



# KNN - delay prediction - actual departure (minus) expected departure.
# MLP - arrival prediction - actual departure.
#   Day of the week, Weekend/weekday, TimeOfArrival, Morning/Midday/Afternoon/Night, Rushhour/noRush


# Time(12:45 = 54513), "Midday" = 0, 1, 0, 0 , "not rushour" => 0, "4 (Friday)" => 54513, 0, 1, 0, 0, 0, 4
# 54513, 0, 1, 0, 0, 0, 4

# 54000, 1, 0, 0, 0, 0, 4
# 12312, 0, 0, 0, 1, 0, 2
# 54513, 0, 1, 0, 0, 1, 4    => arrival_time = 
# # day_segmet = [Morning/Midday/Afternoon/Night]
# day_segmet = [0, 1, 0, 0] => 0, 1, 0, 0
# rush_hour = [Rush/NoRush] => [1, 0] => [0]
# asdsa = [1, 1, 1, 0]
# 

# Norwich 8 delay
# RandomStation = 2 faster
# RandomTwo = 3 faster
# Colchecster = ON TIME