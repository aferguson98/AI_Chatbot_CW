import numpy as np
from sklearn import preprocessing, neighbors
from sklearn.model_selection import train_test_split
import pandas as pd
import csv

class Predictions:

    def __init__(self):
        self.departure_station = ""
        self.arrival_station = ""
        self.time_departure = ""
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
        function to find the corresponding station abbreviation based on the
        provided station from user

        Input:
        station - string of station name - i.e. Ipswich

        Output:
        string - abbreviation of the station provided
        """
        
        x = station.lower()
        print("HellooooO: ", x)
        if x in self.stations:
            print("GOTEM. Value : ", self.stations[x])
            return self.stations[x]

    def knn(self, FROM, TO, Tdepart):
        """
        Finding closest arrival time FROM, TO, TIME departure
        Input:
        FROM - string - departing station
        TO - string - arriving station
        Tdepart - string - time of departure FROM station

        Output:
        string - predicted time of arrival on TO station.
        """
        data = pd.read_csv('../TrainingData/a51/NRCH_LIVST_OD_a51_2019_1_1.csv')
       

        self.departure_station = self.station_finder(FROM)
        self.arrival_station = self.station_finder(TO)
        self.time_departure = Tdepart

        departure_journeys = []
        arrival_journeys = []

        # Loop through the csv file and store specific rows in object.
        for row in data.itertuples():
            # Departing station
            if self.departure_station in row:
                df_dep = data.loc[row.Index]
                departure_journeys.append({ "id" : df_dep.loc['rid'], "arr_at" : df_dep.loc['arr_at'], "dep_at" : df_dep.loc['dep_at']})
                # print(train_journeys)
            # Arriving station
            elif self.arrival_station in row:
                df_arr = data.loc[row.Index]
                arrival_journeys.append({ "id" : df_arr.loc['rid'], "arr_at" : df_arr.loc['arr_at'], "dep_at" : df_arr.loc['dep_at']})
                # print(train_journeys)
        
        # Train the model model
        X = []
        y = []
        for j in range(len(departure_journeys)):
            X.append([departure_journeys[j]['dep_at']])
        for j in range(len(arrival_journeys)):
            y.append([arrival_journeys[j]['arr_at']])
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2)

        clf = neighbors.KNeighborsClassifier()
        clf.fit(X_train, y_train)

        accuracy = clf.score(X_test, y_test)
        print(accuracy)

         
            

        # # public timetable arrival/dedparture, working timetable arrive/departure
        # df = data[['pta', 'ptd', 'wta', 'wtd', 'arr_at']]
        # print(df.head())
        

        
# 1) Write a funct that separates each journey in an object. - Pull all FROM and TO journies into an array so we can use it later.
# 
#   Pull data and turn into object. Store data between given stations FROM and TO. Store only rid, arr_at, dep_at.
#   Run knn - X dep_at ; Y - arr_at  => clf = sklearn.neighbors.KNeighborsClassifier()
#   clf.fit(x_train, y_train)
#   
#   clf.predict(INPUT-time?)


# loop through file, search for FROM
#   until row containing TO in the "tpl" column:
#   store rows that have arr_at != Null
# repeat loop



pr = Predictions()
# pr.station_finder("Norwich")
pr.knn("Diss", "Ipswich", "13:25")

