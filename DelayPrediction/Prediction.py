import numpy as np
from sklearn import preprocessing, neighbors
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import pandas as pd
import csv, os
import datetime

import sys
sys.path.append('../') # This is temporarily here because i just wanna get the database to work for now.
from Database.DatabaseConnector import DBConnection

class Predictions:
    def __init__(self):
        self.departure_station = ""
        self.arrival_station = ""
        self.time_departure = ""
        self.db_connection = DBConnection('AKODatabase.db')
        # self.data = pd.read_csv('..//TrainingData/NRCH_LIVST_OD_a51_2019_2_2.csv')
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
        self.df = [[]]
        # x, y = 0

        # for i in (self.data.rid.unique()):
        #     # Get only those rows that have the same RID
        #     rows_lambda = self.data.apply(lambda x: True if x['rid'] == i else False, axis = 1)
        #     for j in range(len(rows_lambda[rows_lambda == True].index)):
        #         if rows_lambda[rows_lambda == True].any():
        #             journey = { "rid" : i, "tpl" : self.data.tpl, "publicArrive" : self.data.pta, "publicDepart" : self.data.ptd, "actArrive" : self.data.arr_at, "actDedpart" : self.data.dep_at }
        #             self.df.append(journey)
                

   

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
        if x in self.stations:
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
        
        self.departure_station = self.station_finder(FROM)
        self.arrival_station = self.station_finder(TO)
        self.time_departure = Tdepart
 
        departure_journeys = []
        arrival_journeys = []
        t_depart_s = (datetime.datetime.strptime(Tdepart, '%H:%M') - datetime.datetime(1900,1,1)).total_seconds()
        journies = {} # I'm not sure atm if we need this to be sorted, but there's an ordered dict if we need to use it.

        # Make a dict of objects with each journey (RID)
        # Look for journeys that have both FROm and TO dep/arr time (no missing data)
        # Instead of row by row, go by RID from the dictionary
        #   if dep OR arr is NaN, skip the row

        
        # TODO: make this dynamic in the future, for now we know that rids range from 201902017628973 to 201902287629041
        for current_rid in range(201902017628973, 201902287629041):
            
            # Query to extract info from the database by RIDs
            query = "SELECT tpl, pta, ptd, arr_at, dep_at FROM main.TrainingData WHERE rid=?"
            result = self.db_connection.send_query(query, [current_rid]).fetchall()
            
            if not result:
                # This means the rid doesn't exist in the table, so do nothing.
                continue
            
            
            """
                list of dictionaries, link them with rid by by putting them as a dictionary
            """
            # This list will store the dictionary of info about this journey from this specific RID
            current_rid_journey = []
            
            for row in result:
                # Iterate through each row and turn it into a dictionary..
                
                journey_info = {
                    "tpl": row[0], # I'm assuming this was supposed to be named station or sth? TODO: ask Kaloyan
                    "publicArrive": row[1],
                    "publicDepart": row[2],
                    "actArrive": row[3],
                    "acdDepart": row[4]
                }
                
                # And add it to the list
                current_rid_journey.append(journey_info)
            
            # Add this list to the main dictionary, by using the RID as the key
            journies[current_rid] = current_rid_journey 
            
            # We don't need this anymore, but I'm keeping it until we are 100% sure this works.
            """    
            for i in (self.data.rid.unique()):
                journies[x].append(i) # DON'T TOUCH TIHS!
                print(i)
                # Get only those rows that have the same RID
                # rows_lambda = self.data.apply(lambda x: True if x['rid'] == i else False, axis = 1)
                for row in self.data.itertuples():
                    print(len(self.df))
                    print(row)
                    row_index = self.data.loc[row.Index]
                    print(type(row_index))

                    print(type(row_index))

                    if (row_index not in visited_rows):
                        if (row_index['rid'] == i):
                            print("rid matches i")
                            journey = { "rid" : row_index.loc['rid'], "tpl" : row_index.loc['tpl'], "publicArrive" : row_index.loc['pta'], 
                                       "publicDepart" : row_index.loc['ptd'], "actArrive" : row_index.loc['arr_at'], 
                                       "acdDepart" : row_index.loc['dep_at'] }
                            # journey = { "rid" : i, "tpl" : self.data.tpl, "publicArrive" : self.data.pta, "publicDepart" : self.data.ptd, "actArrive" : self.data.arr_at, "actDedpart" : self.data.dep_at }
                            journies= np.append(journies[x], journey)
                        else:
                            break
                    visited_rows.append(row.Index)

                print(self.df[0])
                x += 1
                self.df.append(journies)
                """
        

        # for row in self.data.itertuples():
            
        #     # Departing station
        #     if self.departure_station in row:
        #         df_dep = self.data.loc[row.Index] # get the current row
        #         # Check if the tuple is NOT EMPTY
        #         if ( df_dep.loc['ptd'] == df_dep.loc['ptd'] ) and ( df_dep.loc['dep_at'] == df_dep.loc['dep_at'] ):
        #             # Difference in time between expected departure and actual departure in seconds.
        #             ptd_s = (datetime.datetime.strptime(df_dep.loc['ptd'], '%H:%M') - datetime.datetime(1900,1,1)).total_seconds()
        #             dep_at_s = (datetime.datetime.strptime(df_dep.loc['dep_at'], '%H:%M') - datetime.datetime(1900,1,1)).total_seconds()
        #             # diff_in_sec = dep_at_s - ptd_s
        #             departure_journeys.append({ "id" : df_dep.loc['rid'], "dep_difference" : dep_at_s})
        #     # Arriving station
        #     elif self.arrival_station in row:
        #         if len(arrival_journeys) > len(departure_journeys):
        #             continue

        #         df_arr = self.data.loc[row.Index] # get the current row
        #         # Check if the tuple is NOT EMPTY
        #         if ( df_arr.loc['pta'] == df_arr.loc['pta'] ) and ( df_arr.loc['arr_at'] == df_arr.loc['arr_at'] ):
        #             # Difference in time between expected departure and actual departure in seconds.
        #             pta_s = (datetime.datetime.strptime(df_arr.loc['pta'], '%H:%M') - datetime.datetime(1900,1,1)).total_seconds()
        #             arr_at_s = (datetime.datetime.strptime(df_arr.loc['arr_at'], '%H:%M') - datetime.datetime(1900,1,1)).total_seconds()
        #             # diff_in_sec = arr_at_s - pta_s
        #             arrival_journeys.append({ "id" : df_arr.loc['rid'], "dep_difference" : arr_at_s})

        # X = []
        # y = []
        # # Selecting on specific tuple from the dictionaries - dep_difference
        # for i in range(len(departure_journeys)):
        #     X.append(departure_journeys[i]['dep_difference'])

        # for i in range(len(arrival_journeys)):
        #     y.append(arrival_journeys[i]['dep_difference'])

        # # turn the variables into numpy arrays so they can be reshaped for training the model.
        # X = np.array(X)
        # y = np.array(y)
        # t_depart_s = np.array(t_depart_s)

        # # Splitting data into 80-20 train/test
        # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2)

        # # Reshape the data into 2D arrays so it can be used to train
        # X_train = X_train.reshape(-1, 1)
        # y_train = y_train.reshape(-1, 1)
        # X_test = X_test.reshape(-1, 1)
        # y_test = y_test.reshape(-1, 1)
        # t_depart_s = t_depart_s.reshape(-1, 1)

        # # Specifying type of classification and training
        # clf = neighbors.KNeighborsRegressor()
        # clf.fit(X_train, y_train)

        # mse = mean_squared_error(X_test, y_test)
        # print("Mean squared error is: ", mse)

        # prediction_s = clf.predict(t_depart_s)
        # prediction_h = int(prediction_s[0][0] / 3600)
        # prediction_s = prediction_s - (prediction_h * 3600)
        # prediction_m = int(prediction_s[0][0] / 60)
        # prediction_s = prediction_s - (prediction_m * 60)
        # prediction_s = int(prediction_s[0][0] % 60)

        # print(prediction_h, prediction_m, prediction_s)
        # print("Your journey will be delayed by " + str(prediction_m) + " minutes and " + str(prediction_s) + " seconds.")

        # # Loop through the csv file and store specific rows in object.
        # for row in data.itertuples():
        #     # Departing station
        #     if self.departure_station in row:
        #         df_dep = data.loc[row.Index]
        #         # Check if the tuple is NOT EMPTY
        #         if ( df_dep.loc['arr_at'] == df_dep.loc['arr_at'] ) and ( df_dep.loc['dep_at'] == df_dep.loc['dep_at'] ):
        #             departure_journeys.append({ "id" : df_dep.loc['rid'], "arr_at" : df_dep.loc['arr_at'], "dep_at" : df_dep.loc['dep_at']})
        #         # print(train_journeys)
        #     # Arriving station
        #     elif self.arrival_station in row:
        #         df_arr = data.loc[row.Index]
        #         # Check if the tuple is NOT EMPTY
        #         if ( df_arr.loc['arr_at'] == df_arr.loc['arr_at'] ) and ( df_arr.loc['dep_at'] == df_arr.loc['dep_at'] ):
        #             arrival_journeys.append({ "id" : df_arr.loc['rid'], "arr_at" : df_arr.loc['arr_at'], "dep_at" : df_arr.loc['dep_at']})
        #         # print(train_journeys)
        
        # # Train the model model
        # X = []
        # y = []
        # for j in range(len(departure_journeys)):
        #     b = float(departure_journeys[j]['dep_at'].replace(":", "."))
        #     X.append([b])
        # for j in range(len(arrival_journeys)):
        #     c = float(arrival_journeys[j]['arr_at'].replace(":", "."))
        #     y.append([c])
        
        # # X = np.array(X)
        # # y = np.array(y)

        # if len(X) > len(y):
        #     X = X[:len(y)]
        # elif len(y) > len(X):
        #     y = y[:len(X)]

        # X_encoded = preprocessing.LabelEncoder().fit_transform(X)
        # y_encoded = preprocessing.LabelEncoder().fit_transform(y)

        # X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size = 0.2)

        # clf = neighbors.KNeighborsClassifier()
        # clf.fit(X_train, y_train)

        # accuracy = clf.score(X_test, y_test)
        # print(accuracy)

         
            

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
pr.knn("Norwich", "Diss", "15:38")
