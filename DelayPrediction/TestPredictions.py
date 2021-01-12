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
import pandas as pd
import csv
from datetime import datetime, timedelta
from Database.DatabaseConnector import DBConnection
from difflib import SequenceMatcher, get_close_matches
from DelayPrediction.Prediction import Predictions

class TestPredictions(Predictions):

    def __init__(self):
        super().__init__()


    def test_arrival(self, FROM, TO, Tdepart, size_x):
        self.departure_station = super().station_finder(FROM)
        self.arrival_station = super().station_finder(TO)
        self.time_departure = Tdepart

        result = super().harvest_data()

        X = []
        Y = []
        
        departure_data = [] 
        arrival_data = [] 

        for journey in range(len(result)):
            J = []
            K = []
            if result[journey][2] != '' and result[journey][3] != '' and result[journey][5] != '' and result[journey][6] != '':
                date = str(result[journey][0])
                day_of_week = datetime(int(date[:4]), int(date[4:6]), int(date[6:8])).weekday()
                if size_x == 1:
                    try:
                        X.append((datetime.strptime(result[journey][3], '%H:%M') - datetime(1900,1,1)).total_seconds())
                    except:
                        print("Unable to convert DEPARTURE to seconds")
                    try:
                        Y.append((datetime.strptime(result[journey][6], '%H:%M') - datetime(1900,1,1)).total_seconds())
                    except:
                        print("Unable to convert ARRIVAL to seconds")
                elif size_x == 2:
                    try:
                        J.append(day_of_week)
                        J.append((datetime.strptime(result[journey][3], '%H:%M') - datetime(1900,1,1)).total_seconds())
                        X.append(J)
                    except:
                        print("Unable to convert DEPARTURE to seconds")
                    try:
                        K.append(day_of_week)
                        K.append((datetime.strptime(result[journey][6], '%H:%M') - datetime(1900,1,1)).total_seconds())
                        Y.append(K)
                    except:
                        print("Unable to convert ARRIVAL to seconds")


        knn_arrival = self.test_knn(X, Y, size_x)
        arrival_time = super().convert_time(knn_arrival)

        svm_arr = self.test_svm(X,Y, size_x)
        svm_arr_time = super().convert_time([svm_arr])

        rf_arr = self.test_random_forest(X, Y, size_x)
        rf_arr_time = super().convert_time([rf_arr])

        mlp_arrive = self.test_mlp(X, Y, size_x)
        mlp_arrival_time = super().convert_time([mlp_arrive])

        print("------Arrival-------")
        print("KNN: "+str(arrival_time[0]).zfill(2) + ":" + str(arrival_time[1]).zfill(2) + ":" + str(arrival_time[2]).zfill(2))
        print("SVM: "+str(svm_arr_time[0]).zfill(2) + ":" + str(svm_arr_time[1]).zfill(2)+ ":" + str(svm_arr_time[2]).zfill(2))
        print("RF: "+str(rf_arr_time[0]).zfill(2) + ":" + str(rf_arr_time[1]).zfill(2)+ ":" + str(rf_arr_time[2]).zfill(2))
        print("MLP: "+str(mlp_arrival_time[0]).zfill(2) + ":" + str(mlp_arrival_time[1]).zfill(2)+ ":" + str(mlp_arrival_time[2]).zfill(2))

    def tesprediction_inputelay(self, FROM, TO, Tdepart, size_x):

        self.departure_station = super().station_finder(FROM)
        self.arrival_station = super().station_finder(TO)
        self.time_departure = Tdepart
        
        result = super().harvest_data()
        X = []
        Y = []

        for journey in range(len(result)):
            J = []
            K = []
            if result[journey][2] != '' and result[journey][3] != '' and result[journey][5] != '' and result[journey][6] != '':
                date = str(result[journey][0])
                day_of_week = datetime(int(date[:4]), int(date[4:6]), int(date[6:8])).weekday()
                if size_x == 1:
                    try:
                        X.append((datetime.strptime(result[journey][3], '%H:%M') - datetime(1900,1,1)).total_seconds() - 
                                (datetime.strptime(result[journey][2], '%H:%M') - datetime(1900,1,1)).total_seconds())
                    except:
                        print("Unable to convert DEPARTURE to seconds")
                    try:
                        Y.append((datetime.strptime(result[journey][6], '%H:%M') - datetime(1900,1,1)).total_seconds() - 
                                (datetime.strptime(result[journey][5], '%H:%M') - datetime(1900,1,1)).total_seconds())
                    except:
                        print("Unable to convert ARRIVAL to seconds")
                elif size_x == 2:
                    try:
                        J.append(day_of_week)
                        J.append((datetime.strptime(result[journey][3], '%H:%M') - datetime(1900,1,1)).total_seconds() - 
                                (datetime.strptime(result[journey][2], '%H:%M') - datetime(1900,1,1)).total_seconds())
                        X.append(J)
                    except:
                        print("Unable to convert DEPARTURE to seconds")
                    try:
                        K.append(day_of_week)
                        K.append((datetime.strptime(result[journey][6], '%H:%M') - datetime(1900,1,1)).total_seconds() - 
                                (datetime.strptime(result[journey][5], '%H:%M') - datetime(1900,1,1)).total_seconds())
                        Y.append(K)
                    except:
                        print("Unable to convert ARRIVAL to seconds")
                

        knn_delay = self.test_knn(X, Y, size_x)
        knn_delay_time = super().convert_time(knn_delay)

        svm_delay = self.test_svm(X, Y, size_x)
        svm_delay_time = super().convert_time([svm_delay])

        rf_delay = self.test_random_forest(X, Y, size_x)
        rf_delay_time = super().convert_time([rf_delay])


        print("-------Delay-------")
        print("KNN: "+str(knn_delay_time[0]).zfill(2) + ":" + str(knn_delay_time[1]).zfill(2) + ":" + str(knn_delay_time[2]).zfill(2))
        print("SVM: "+str(svm_delay_time[0]).zfill(2) + ":" + str(svm_delay_time[1]).zfill(2)+ ":" + str(svm_delay_time[2]).zfill(2))
        print("RF: "+str(rf_delay_time[0]).zfill(2) + ":" + str(rf_delay_time[1]).zfill(2)+ ":" + str(rf_delay_time[2]).zfill(2))
        

    def test_knn(self, x_data, y_data, size_x):
        
        time_depart_s = (datetime.strptime(self.time_departure, '%H:%M') - datetime(1900,1,1)).total_seconds()
        prediction_input = []
        if size_x == 2:
            prediction_input.append(self.day_of_week)
        prediction_input.append(time_depart_s)

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

        counter = 0
        i = 0
        if size_x == 2:
            for data in X_test:
                data = data.reshape(-1, 1)
                if abs((clf.predict(data) - y_test[i])) <= 60:
                    counter += 1
                i += 1
            print("KNN accuracy:", (counter / len(X_test) * 100))
            

        prediction_s = clf.predict(prediction_input)

        return prediction_s


    def test_svm(self, x_data, y_data, size_x):
        time_depart_s = (datetime.strptime(self.time_departure, '%H:%M') - datetime(1900,1,1)).total_seconds()
        prediction_input = []
        if size_x == 2:
            prediction_input.append(self.day_of_week)
        prediction_input.append(time_depart_s)
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
        clf = svm.SVC(kernel = 'linear', gamma = 0.0001)
        clf.fit(X_train, y_train.ravel())

        counter = 0
        i = 0
        if size_x == 2:
            for data in X_test:
                data = data.reshape(-1, 1)
                if abs((clf.predict(data) - y_test[i])) <= 60:
                    counter += 1
                i += 1
            print("SVN accuracy:", (counter / len(X_test) * 100))
            

        prediction_s = clf.predict(prediction_input)

        return prediction_s


    def test_random_forest(self, x_data, y_data, size_x):
        
        time_depart_s = (datetime.strptime(self.time_departure, '%H:%M') - datetime(1900,1,1)).total_seconds()
        prediction_input = []
        if size_x == 2:
            prediction_input.append(self.day_of_week)
        prediction_input.append(time_depart_s)

        X = np.array(x_data)
        Y = np.array(y_data)
        prediction_input = np.array(time_depart_s)

        X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size = 0.2)

        X_train = X_train.reshape(-1, 1)
        y_train = y_train.reshape(-1, 1)
        X_test = X_test.reshape(-1, 1)
        y_test = y_test.reshape(-1, 1)
        prediction_input = prediction_input.reshape(-1, 1)

        clf = RandomForestClassifier(n_estimators = 100)
        clf.fit(X_train, y_train.ravel())

        counter = 0
        i = 0
        if size_x == 2:
            for data in X_test:
                data = data.reshape(-1, 1)
                if abs((clf.predict(data) - y_test[i])) <= 60:
                    counter += 1
                i += 1
            print("RF accuracy:", (counter / len(X_test) * 100))


        prediction_s = clf.predict(prediction_input)

        return prediction_s

    def test_mlp(self, x_data, y_data, size_x):
        # Multi-layer perception
        time_depart_s = (datetime.strptime(self.time_departure, '%H:%M') - datetime(1900,1,1)).total_seconds()
        prediction_input = []
        if size_x == 2:
            prediction_input.append(self.day_of_week)
        prediction_input.append(time_depart_s)

        X = np.array(x_data)
        Y = np.array(y_data)
        prediction_input = np.array(time_depart_s)

        X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size = 0.2)

        X_train = X_train.reshape(-1, 1)
        y_train = y_train.reshape(-1, 1)
        X_test = X_test.reshape(-1, 1)
        y_test = y_test.reshape(-1, 1)
        prediction_input = prediction_input.reshape(-1, 1)


        clf = MLPRegressor(hidden_layer_sizes = (32,16,8), activation="relu", solver="adam", random_state=1, max_iter = 2000)
        clf.fit(X_train, y_train.ravel())

        prediction_s = clf.predict(prediction_input)

        return prediction_s





test = TestPredictions()
depart = "14:45"
print("Departing at:", depart)

print("Arrival x == 1:")
test.test_arrival("Norwich", "Colchester", depart, 1)
print("Arrival x == 2:")
test.test_arrival("Norwich", "Colchester", depart, 2)

print("Delay x == 1:")
test.tesprediction_inputelay("Norwich", "Colchester", depart, 1)
print("Delay x == 2:")
test.tesprediction_inputelay("Norwich", "Colchester", depart, 2)