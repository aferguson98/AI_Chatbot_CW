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
        self.harvest_data()


    def harvest_data(self):
        """

        Get all CSV file data from the database and returns it as object

        """
        
        query = "SELECT DISTINCT rid FROM main.TrainingData"
        list_of_rids = self.db_connection.send_query(query).fetchall()

        for current_rid in list_of_rids:
            
            # Query to extract info from the database by RIDs
            query = "SELECT tpl, pta, ptd, arr_at, dep_at FROM main.TrainingData WHERE rid=?"
            result = self.db_connection.send_query(query, [current_rid[0]]).fetchall()

            # This list will store the dictionary of info about this journey from this specific RID
            current_rid_journey = []
            
            for row in result:
                # Iterate through each row and turn it into a dictionary..
                journey_info = {
                    "station": row[0],
                    "publicArrival": row[1],
                    "publicDepart": row[2],
                    "actArrival": row[3],
                    "actDepart": row[4]
                }
                
                # And add it to the list
                current_rid_journey.append(journey_info)
            
            # Add this list to the main dictionary, by using the RID as the key
            self.journeys[current_rid[0]] = current_rid_journey

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


    def knn(self, FROM, TO, Tdepart):
        """
        Finding closest arrival time FROM, TO, TIME departure
        Parameters
        ----------
        FROM: string 
            departing station
        TO: string 
            arriving station
        Tdepart: string
            time of departure FROM station

        Returns
        -------
        string:
            predicted time of arrival on TO station.
        """
        
        self.departure_station = self.station_finder(FROM)
        self.arrival_station = self.station_finder(TO)
        self.time_departure = Tdepart
 
        departure_data = []
        arrival_data = []
        t_depart_s = (datetime.datetime.strptime(Tdepart, '%H:%M') - datetime.datetime(1900,1,1)).total_seconds()
        

        for i in self.journeys:
            dep_args = (i, self.departure_station)
            arr_args = (i, self.arrival_station)
            has_dep = "SELECT tpl, ptd, arr_at, dep_at FROM main.TrainingData WHERE rid = ? AND tpl = ? AND dep_at IS NOT NULL"
            has_arr = "SELECT tpl, pta, arr_at, dep_at FROM main.TrainingData WHERE rid = ? AND tpl = ? AND arr_at IS NOT NULL"
            dep_has_values = self.db_connection.send_query(has_dep, dep_args).fetchall()
            arr_has_values = self.db_connection.send_query(has_arr, arr_args).fetchall()

            if (dep_has_values[0][3] != '') and (arr_has_values[0][3] != ''):
                for j in self.journeys[i]:
                    if j['station'] == self.departure_station:
                        departure_data.append(j['actDepart'])
                    elif j['station'] == self.arrival_station:
                        arrival_data.append(j['actArrival'])
            else:
                continue
                


        # Change string values in the departure data to flaot so they can be plotted
        X = []
        Y = []
        for i in range(len(departure_data)):
            try:
                a = float(departure_data[i].replace(":", "."))
                X.append(a)
            except:
                print("Unable to convert string")
                departure_data[i] = '0.0' + departure_data[i]
                a = float(departure_data[i])
                X.append(a)
        for j in range(len(arrival_data)):
            try:
                b = float(arrival_data[j].replace(":","."))
                Y.append(b)
            except:
                print("Unable to convert string")
                arrival_data[j] = '0.0' + arrival_data[j]
                b = float(arrival_data[j])
                Y.append(b)

        # turn the variables into numpy arrays so they can be reshaped for training the model.
        X = np.array(X)
        Y = np.array(Y)
        t_depart_s = np.array(t_depart_s)

        # Splitting data into 80-20 train/test
        X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size = 0.2)

        # Reshape the data into 2D arrays so it can be used to train
        X_train = X_train.reshape(-1, 1)
        y_train = y_train.reshape(-1, 1)
        X_test = X_test.reshape(-1, 1)
        y_test = y_test.reshape(-1, 1)
        t_depart_s = t_depart_s.reshape(-1, 1)

        # Specifying type of classification and training
        clf = neighbors.KNeighborsRegressor()
        clf.fit(X_train, y_train)


        accuracy = clf.score(X_test, y_test)
        print("accuracy:" , accuracy)
        mse = mean_squared_error(X_test, y_test)
        print("Mean squared error is: ", mse)

        prediction_s = clf.predict(t_depart_s)
        prediction_h = int(prediction_s[0][0] / 3600)
        prediction_s = prediction_s - (prediction_h * 3600)
        prediction_m = int(prediction_s[0][0] / 60)
        prediction_s = prediction_s - (prediction_m * 60)
        prediction_s = int(prediction_s[0][0] % 60)

        print("hh: "+ str(prediction_h) + " mm: " + str(prediction_m) + " ss:" + str(prediction_s))
        if (prediction_h == 0) and (prediction_m == 0):
            print("Your journey is expected to be delayed by less than a minute.")
        else:
            print("Your journey is expected to be delayed by " + str(prediction_m) + " minutes and " + str(prediction_s) + " seconds.")


pr = Predictions()
# pr.station_finder("Norwich")
pr.knn("Norwich", "Colchester", "11:30")
