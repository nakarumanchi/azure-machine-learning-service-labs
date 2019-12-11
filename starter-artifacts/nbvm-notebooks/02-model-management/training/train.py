import argparse
import os
import numpy as np
import pandas as pd

from sklearn import linear_model 
from sklearn.externals import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score

from azureml.core import Run
from sklearn.model_selection import train_test_split

# let user feed in 2 parameters, the location of the data files (from datastore), and the training set percentage to use
parser = argparse.ArgumentParser()
parser.add_argument('--data-folder', type=str, dest='data_folder', help='data folder mounting point')
parser.add_argument('--training-set-percentage', type=float, dest='training_set_percentage', default=0.25, help='percentage of dataset to use for training')
args = parser.parse_args()

data_folder = os.path.join(args.data_folder, 'used_cars')
print('Data folder:', data_folder)
data_csv_path = os.path.join(data_folder, 'UsedCars_Affordability.csv')
print('Path to CSV file dataset:' + data_csv_path)

# Load the data
df_affordability = pd.read_csv(data_csv_path)
full_X = df_affordability[["Age", "KM"]]
full_Y = df_affordability[["Affordable"]]

def train_eval_register_model(full_X, full_Y,training_set_percentage):

    # Acquire the current run
    run = Run.get_context()

    train_X, test_X, train_Y, test_Y = train_test_split(full_X, full_Y, 
                                                        train_size=training_set_percentage, 
                                                        test_size=1.0-training_set_percentage, 
                                                        random_state=42)

    train_X = train_X.values.astype(float)
    train_Y = train_Y.values.ravel()
    test_X = test_X.values.astype(float)
    test_Y = test_Y.values.ravel()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(train_X)
    clf = linear_model.LogisticRegression(C=1, solver='lbfgs')
    clf.fit(X_scaled, train_Y)

    scaled_inputs = scaler.transform(test_X)
    predictions = clf.predict(scaled_inputs)
    score = accuracy_score(test_Y, predictions)

    print("With %0.2f percent of data, model accuracy reached %0.4f." % (training_set_percentage, score))

    # Log the training metrics to Azure Machine Learning service run history
    run.log("Training_Set_Percentage", training_set_percentage)
    run.log("Accuracy", score)

    # note file saved in the outputs folder is automatically uploaded into experiment record
    joblib.dump(value=clf, filename='outputs/model.pkl')
    
    run.complete()
    
    return (clf, score)


training_set_percentage = 0.75
model, score = train_eval_register_model(full_X, full_Y, training_set_percentage)





