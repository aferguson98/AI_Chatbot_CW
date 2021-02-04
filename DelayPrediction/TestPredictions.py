import sys, os
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import numpy as np
from sklearn import preprocessing, neighbors, svm
from sklearn import metrics
from sklearn.metrics import mean_squared_error, f1_score, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neural_network import MLPRegressor, MLPClassifier
import pandas as pd
import csv
from datetime import datetime, timedelta
from Database.DatabaseConnector import DBConnection
from difflib import SequenceMatcher, get_close_matches
from DelayPrediction.newPrediction import Predictions

class TestPredictions(Predictions):

    def __init__(self):
        super().__init__()

    def prepare_datasets(self, x):
        result = super().harvest_data()
        data = []

        for journey in range(len(result)):
            if (result[journey][2] != '' and result[journey][3] != '' and 
                    result[journey][5] != '' and result[journey][6] != ''):
                rid = str(result[journey][0])
                day_of_week = datetime(int(rid[:4]), int(rid[4:6]),
                                        int(rid[6:8])).weekday()
                hour_of_day = int(result[journey][3].split(":")[0])
                minute_of_day = int(result[journey][3].split(":")[1])
                weekend = super().is_weekend(day_of_week)
                day_segment = super().check_day_segment(hour_of_day)
                rush_hour = super().is_rush_hour(hour_of_day, minute_of_day)
                try:
                    time_dep = (datetime.strptime(result[journey][3], '%H:%M') -
                                datetime(1900, 1, 1)).total_seconds()
                except:
                    print("Unable to get time_dep")
                try:
                    journey_delay = ((datetime.strptime(result[journey][3], '%H:%M') -
                                datetime(1900, 1, 1)).total_seconds() -
                                (datetime.strptime(result[journey][2], '%H:%M') -
                                datetime(1900, 1, 1)).total_seconds())
                except:
                    print("Unable to get journey_delay")
                try:
                    time_arr = ((datetime.strptime(result[journey][6], '%H:%M') -
                                    datetime(1900, 1, 1)).total_seconds() -
                                    (datetime.strptime(result[journey][5], '%H:%M') -
                                    datetime(1900, 1, 1)).total_seconds())
                except:
                    print("Unable to get  time_arrival")
                if x == 2:
                    data.append([rid, time_dep, journey_delay, day_of_week,  time_arr])
                elif x == 3:
                    data.append([rid, time_dep, journey_delay, day_of_week, weekend,
                                    time_arr])
                elif x == 4:
                    data.append([rid, time_dep, journey_delay, day_of_week, weekend,
                                     day_segment, time_arr])
                elif x == 5:
                    data.append([rid, time_dep, journey_delay, day_of_week, 
                                weekend, day_segment, rush_hour,  time_arr])
        return data

    def predict_nn(self, data, num_x):
        dep_time_s = (datetime.strptime(self.exp_dep, '%H:%M') - datetime(
                            1900, 1, 1)).total_seconds()
        delay_s = int(self.delay) * 60

        if num_x == 2:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay","day_of_week", "arrival_time"])
        elif num_x == 3:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay","day_of_week","weekend", "arrival_time"])
        elif num_x == 4:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay","day_of_week","weekend",
                            "day_segment", "arrival_time"])
        elif num_x == 5:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay", "day_of_week","weekend", 
                            "day_segment", "rush_hour", "arrival_time"])
        

        X = journeys.drop(['rid','arrival_time'], axis=1)
        y = journeys['arrival_time'].values
        
        x_training_data, x_test_data, y_training_data, y_test_data = train_test_split(X, y, test_size = 0.3, random_state=5)
        
        clf = neighbors.NearestNeighbors(n_neighbors=1)
        clf.fit(x_training_data)

        counter = 0
        i = 0
        for row in x_test_data.iterrows():
            time = row[1][0]
            delay  = row[1][1]
            if num_x == 2:
                day_of_week = row[1][2]
                predict = clf.kneighbors([[time, delay, day_of_week]])
            if num_x == 3:
                day_of_week = row[1][2]
                weekend = row[1][3]
                predict = clf.kneighbors([[time, delay, day_of_week, weekend]])
            if num_x == 4:
                day_of_week = row[1][2]
                weekend = row[1][3]
                day_segment = row[1][4]
                predict = clf.kneighbors([[time, delay, day_of_week, weekend, day_segment]])
            if num_x == 5:
                day_of_week = row[1][2]
                weekend = row[1][3]
                day_segment = row[1][4]
                rush_hour = row[1][5]
                predict = clf.kneighbors([[time, delay, day_of_week, weekend, day_segment, rush_hour]])

            predict_arrival = y_training_data[predict[1]][0][0]
            p_time = x_training_data.iloc[predict[1][0][0]][0]
            p_delay = x_training_data.iloc[predict[1][0][0]][1]
            if abs(y_test_data[i] - predict_arrival ) <= 60:
                counter += 1
            i += 1

        y_pred = clf.kneighbors(x_test_data)
        print("NN accuracy w/ user input:", (counter / len(x_test_data) * 100))
        # print("NN r2:", metrics.r2_score(y_test_data,y_pred) * 100)
        # print("NN f1_score", f1_score(y_test_data, y_pred, average="weighted") * 100)
        # print("NN MSE:", mean_squared_error(y_test_data, y_pred) / 60)

    def predict_knn(self, data, num_x):
        dep_time_s = (datetime.strptime(self.exp_dep, '%H:%M') - datetime(
                            1900, 1, 1)).total_seconds()
        delay_s = int(self.delay) * 60

        if num_x == 2:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay","day_of_week", "arrival_time"])
        elif num_x == 3:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay","day_of_week","weekend", "arrival_time"])
        elif num_x == 4:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay","day_of_week","weekend",
                            "day_segment", "arrival_time"])
        elif num_x == 5:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay", "day_of_week","weekend", 
                            "day_segment", "rush_hour", "arrival_time"])
        

        X = journeys.drop(['rid','arrival_time'], axis=1)
        y = journeys['arrival_time'].values
        
        x_training_data, x_test_data, y_training_data, y_test_data = train_test_split(X, y, test_size = 0.3, random_state=5)
        
        clf = neighbors.KNeighborsRegressor(n_neighbors= 3)
        clf.fit(x_training_data, y_training_data)

        y_pred = clf.predict(x_test_data)
        
        print("KNN accuracy", accuracy_score(y_test_data, y_pred) * 100)
        print("KNN r2:", metrics.r2_score(y_test_data,y_pred) * 100)
        print("KNN f1_score", f1_score(y_test_data, y_pred, average="weighted") * 100)
        print("KNN RMSE:", np.sqrt(mean_squared_error(y_test_data, y_pred)))


   
    def predict_svm(self, data, num_x):
        dep_time_s = (datetime.strptime(self.exp_dep, '%H:%M') - datetime(
                            1900, 1, 1)).total_seconds()
        delay_s = int(self.delay) * 60
        if num_x == 2:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay","day_of_week", "arrival_time"])
        elif num_x == 3:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay","day_of_week","weekend", "arrival_time"])
        elif num_x == 4:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay","day_of_week","weekend",
                            "day_segment", "arrival_time"])
        elif num_x == 5:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay", "day_of_week","weekend", 
                            "day_segment", "rush_hour", "arrival_time"])
    

        X = journeys.drop(['rid','arrival_time'], axis=1)
        y = journeys['arrival_time'].values
        
        x_training_data, x_test_data, y_training_data, y_test_data = train_test_split(X, y, test_size = 0.3, random_state=42)
        
        clf = svm.LinearSVC(max_iter=200000)
        clf.fit(x_training_data, y_training_data)

        y_pred = clf.predict(x_test_data)
        print("SVM accuracy:", accuracy_score(y_test_data, y_pred)  *  100)
        print("SVM r2:", metrics.r2_score(y_test_data,y_pred) * 100)
        print("SVm f1_score", f1_score(y_test_data, y_pred, average="weighted") * 100)
        print("SVM RMSE", np.sqrt(mean_squared_error(y_test_data, y_pred)))

    def predict_rf(self, data, num_x):
        dep_time_s = (datetime.strptime(self.exp_dep, '%H:%M') - datetime(
                            1900, 1, 1)).total_seconds()
        delay_s = int(self.delay) * 60
        if num_x == 2:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay","day_of_week", "arrival_time"])
        elif num_x == 3:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay","day_of_week","weekend", "arrival_time"])
        elif num_x == 4:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay","day_of_week","weekend",
                            "day_segment", "arrival_time"])
        elif num_x == 5:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay", "day_of_week","weekend", 
                            "day_segment", "rush_hour", "arrival_time"])

        X = journeys.drop(['rid','arrival_time'], axis=1)
        y = journeys['arrival_time'].values
        
        x_training_data, x_test_data, y_training_data, y_test_data = train_test_split(X, y, test_size = 0.3, random_state=5)
        
        clf = RandomForestClassifier(n_estimators = 100)
        clf.fit(x_training_data, y_training_data)

        y_pred = clf.predict(x_test_data)
        print("RF acc_sc:", accuracy_score(y_test_data, y_pred) * 100)
        print("RF r2:", metrics.r2_score(y_test_data,y_pred) * 100)
        print("RF f1_score", f1_score(y_test_data, y_pred, average="weighted") * 100)
        print("RF RMSE", np.sqrt(mean_squared_error(y_test_data, y_pred)))
        
        # print("KNN MSE  is :", ((mse_total / mse_counter) / 60))

    def predict_mlp(self, data, num_x):
        dep_time_s = (datetime.strptime(self.exp_dep, '%H:%M') - datetime(
                            1900, 1, 1)).total_seconds()
        delay_s = int(self.delay) * 60
        if num_x == 2:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay","day_of_week", "arrival_time"])
        elif num_x == 3:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay","day_of_week","weekend", "arrival_time"])
        elif num_x == 4:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay","day_of_week","weekend",
                            "day_segment", "arrival_time"])
        elif num_x == 5:
            journeys = pd.DataFrame(data, columns=["rid", "time_dep", 
                            "delay", "day_of_week","weekend", 
                            "day_segment", "rush_hour", "arrival_time"])

        X = journeys.drop(['rid','arrival_time'], axis=1)
        y = journeys['arrival_time'].values
        
        x_training_data, x_test_data, y_training_data, y_test_data = train_test_split(X, y, test_size = 0.3, random_state=5)
        
        clf = MLPClassifier(hidden_layer_sizes = (32,16,8), activation="relu", solver="adam", random_state=1, max_iter = 5000)
        clf.fit(x_training_data, y_training_data.ravel())

        y_pred = clf.predict(x_test_data)
        print("MLP acc_sc:", accuracy_score(y_test_data, y_pred) * 100)
        print("MLP r2:", metrics.r2_score(y_test_data, y_pred) * 100)
        print("MLP f1_score", f1_score(y_test_data, y_pred, average="weighted") * 100)
        print("MLP RMSE:", np.sqrt(mean_squared_error(y_test_data, y_pred)))

    def run_tests(self):
        depart = "22:00"
        FROM = "Norwich"
        TO = "Manningtree"
        delay = 12
        x = 5

        print("Departing at:", depart)
        print("Number of inputs", x)

        self.departure_station = super().station_finder(FROM)
        self.arrival_station = super().station_finder(TO)
        self.exp_dep = depart
        self.delay = delay
        hour_of_day = int(depart.split(":")[0])
        minute_of_day = int(depart.split(":")[1])
        self.segment_of_day = super().check_day_segment(hour_of_day)
        self.rush_hour = super().is_rush_hour(hour_of_day, minute_of_day)
        data = self.prepare_datasets(x)
        # self.predict_nn(data, x)
        # self.predict_knn(data, x)
        self.predict_svm(data, x)
        # self.predict_rf(data, x)
        # self.predict_mlp(data, x)

test = TestPredictions()
test.run_tests()