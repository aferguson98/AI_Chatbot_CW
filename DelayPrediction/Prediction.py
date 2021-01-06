import sys, os
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import numpy as np
from sklearn import preprocessing, neighbors
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import pandas as pd
import csv
import datetime
from Database.DatabaseConnector import DBConnection

class Predictions:
    def __init__(self):
        self.departure_station = ""
        self.arrival_station = ""
        self.time_departure = ""
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
        if x in self.stations:
            return self.stations[x]


    def harvest_data(self):
        """
        Pulls all journeys from DB that have FROM and TO station and don't have null values as arrival/departure times
        """
      
        query = """SELECT rid_FROM, tpl_FROM, ptd, dep_at, tpl_TO, pta, arr_at FROM
                            (SELECT rid AS rid_FROM, tpl AS tpl_FROM, ptd, dep_at FROM main.March2019Data 
                            WHERE tpl = '{0}'
                            AND dep_at IS NOT NULL
                            AND ptd IS NOT NULL
                            ) AS x
                            JOIN
                            (SELECT rid AS rid_TO, tpl AS tpl_TO, pta, arr_at FROM main.March2019Data 
                            WHERE tpl = '{1}'
                            AND arr_at IS NOT NULL
                            AND pta IS NOT NULL
                            ) AS y on x.rid_FROM = y.rid_TO
                        ORDER BY rid_FROM """.format(self.departure_station, self.arrival_station)
   
        result = self.db_connection.send_query(query).fetchall()
        return result

    def predict(self, x_data, y_data):
        """
            KNN prediction

            Parameters
            ----------
            x_data - array
                Data serving as input
            y_data - array
                Data serving as output
            time - str
                Time when user has departed station

            Returns
            -------
            Predicted value based on the input - time user will be delayed OR estimated arrival time to X station
        """
        
        t_depart_s = (datetime.datetime.strptime(self.time_departure, '%H:%M') - datetime.datetime(1900,1,1)).total_seconds()

        # turn the variables into numpy arrays so they can be reshaped for training the model.
        X = np.array(x_data)
        Y = np.array(y_data)
        t_d = np.array(t_depart_s)

        # Splitting data into 80-20 train/test
        X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size = 0.2)

        # Reshape the data into 2D arrays so it can be used to train
        X_train = X_train.reshape(-1, 1)
        y_train = y_train.reshape(-1, 1)
        X_test = X_test.reshape(-1, 1)
        y_test = y_test.reshape(-1, 1)
        t_d = t_d.reshape(-1, 1)

        # Specifying type of classification and training
        clf = neighbors.KNeighborsRegressor()
        clf.fit(X_train, y_train)


        accuracy = clf.score(X_test, y_test)
        print("accuracy:" , accuracy)
        mse = mean_squared_error(X_test, y_test)
        print("Mean squared error is: ", mse)

        prediction_s = clf.predict(t_d)

        return prediction_s


    def convert_time(self, time):
        """
        Convert given time (in seconds) to hours, minutes, seconds
        """
        tt = []
        hh = int(time[0][0] / 3600)
        tt.append(hh)
        time = time - (hh * 3600)
        mm = int(time[0][0] / 60)
        tt.append(mm)
        time = time - (mm * 60)
        ss = int(time[0][0] % 60)
        tt.append(ss)

        return tt

    def predict_delay(self):

        result = self.harvest_data()
 
        departure_data = [] # Departure time for all cases of departure_station
        arrival_data = [] # Arrival time for all cases of arrival_station
        X = []
        Y = []

        for journey in range(len(result)):
            #    public_departure            actual_departure              public_arrival               actual_arrival
            if result[journey][2] != '' and result[journey][3] != '' and result[journey][5] != '' and result[journey][6] != '':
                # Add (actual departure - expected departure) in seconds to X
                try:
                    X.append((datetime.datetime.strptime(result[journey][3], '%H:%M') - datetime.datetime(1900,1,1)).total_seconds() - 
                            (datetime.datetime.strptime(result[journey][2], '%H:%M') - datetime.datetime(1900,1,1)).total_seconds())
                except:
                    print("Unable to convert DEPARTURE to seconds")
                # Add (actual arrival - expected arrival) in seconds to Y
                try:
                    Y.append((datetime.datetime.strptime(result[journey][6], '%H:%M') - datetime.datetime(1900,1,1)).total_seconds() - 
                            (datetime.datetime.strptime(result[journey][5], '%H:%M') - datetime.datetime(1900,1,1)).total_seconds())
                except:
                    print("Unable to convert ARRIVAL to seconds")
                

        prediction_s = self.predict(X, Y)
        converted_time = self.convert_time(prediction_s)

        return converted_time


    def predict_arrival(self, FROM, TO, Tdepart):
        """
        Predicting when the train will arrive at the TO station

        """
        self.departure_station = self.station_finder(FROM)
        self.arrival_station = self.station_finder(TO)
        self.time_departure = Tdepart

        result = self.harvest_data()

        X = []
        Y = []
        departure_data = [] # Departure time for all cases of departure_station
        arrival_data = [] # Arrival time for all cases of arrival_station

        for journey in range(len(result)):
            # public_departure              actual_departure              public_arrival               actual_arrival
            if result[journey][2] != '' and result[journey][3] != '' and result[journey][5] != '' and result[journey][6] != '':
                # Add actual departurein seconds to X
                try:
                    X.append((datetime.datetime.strptime(result[journey][3], '%H:%M') - datetime.datetime(1900,1,1)).total_seconds())
                except:
                    print("Unable to convert DEPARTURE to seconds")
                # Add actual arrival in seconds to Y
                try:
                    Y.append((datetime.datetime.strptime(result[journey][6], '%H:%M') - datetime.datetime(1900,1,1)).total_seconds())
                except:
                    print("Unable to convert ARRIVAL to seconds")

        arrival = self.predict(X, Y)
        delay_time = self.predict_delay()
        arrival_time = self.convert_time(arrival)
        
        if (delay_time[0] == 0) and (delay_time[1] == 0):
            print("Your journey is expected to be delayed by less than a minute. You will arrive at " + TO +  " at " + str(arrival_time[0]) 
                + ":" + str(arrival_time[1]))
        elif delay_time[0] == 0:
            print("Your journey is expected to be delayed by " + str(delay_time[1]) + " minutes and " + str(delay_time[2]) + 
                " seconds. You will arrive at " + TO +  " at " + str(arrival_time[0]) + ":" + str(arrival_time[1]))


pr = Predictions()
# pr.station_finder("Norwich")
pr.predict_arrival("Norwich", "Colchester", "14:45")



# I'm late from Norwich. -> Where to? -> DISS 

# Actual_dep - planned_departure. Store in X.

# SVN training? Try few modals and see which one performs how. Write about your findings


# TO DO:
# 1)Get similar cities based on name
# 2)Use more data (look library for checking day of year based on date.)
