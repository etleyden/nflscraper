import sys
import pandas as pd
import numpy as np
from tqdm import tqdm
from neural_network import NN

from sklearn.impute import KNNImputer
from sklearn import tree
from sklearn.svm import SVC
from sklearn.model_selection import KFold
from sklearn.metrics import f1_score, accuracy_score

import torch
import torch.nn as nn
import torch.optim as optim

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}")

def preprocess(df):
    # 1. Drop game_ids
    df.drop('game_id', axis=1, inplace=True)
    # 2. Change labels from Home | Away to -1 | 1, respectively
    df["label"] = df["label"].map({"Home": 0, "Away": 1})

    # TODO: test that this actually works
    imputer = KNNImputer(n_neighbors=10, weights="uniform")
    if 'precip_severity' in df.columns: df["precip_severity"] = imputer.fit_transform(df[["precip_severity"]])
    if 'temperature' in df.columns: df["temperature"] = imputer.fit_transform(df[["temperature"]])


    # 3. normalize columns
    data = df.drop(['label'], axis=1)
    for column in data.columns:
        data[column] = (data[column] - data[column].min()) / (data[column].max() - data[column].min())

    return data, df["label"]


def main():
    if len(sys.argv) > 1:
        fpath = sys.argv[1]
    else:
        print("Usage: python train_model.py [train.csv]")
        sys.exit(1)
    csv_data = pd.read_csv(fpath)
    X, y = preprocess(csv_data)

    # models
    dt, dt_score, dt_acc = tree.DecisionTreeClassifier(), [], []
    svm, svm_score, svm_acc = SVC(), [], []
    nn, nn_score, nn_acc = NN(len(X.columns), device=device), [], []

    # repeated five fold cross validation to smooth the accuracy measure between runs
    # NOTE: non-repeating five fold cross validation is highly sensitive to the split in the data, 
    #   so new shuffles each time helps give more consistent results between runs
    for j in tqdm(range(15), position=0):
        kf = KFold(n_splits=5, shuffle=True)
        for i, (train_idx, test_idx) in tqdm(enumerate(kf.split(X)), total=5, position=1, leave=False):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            dt.fit(X_train, y_train)
            dt_pred = dt.predict(X_test)
            dt_score.append(f1_score(y_test, dt_pred))
            dt_acc.append(accuracy_score(y_test, dt_pred))

            svm.fit(X_train, y_train)
            svm_pred = svm.predict(X_test)
            svm_score.append(f1_score(y_test, svm_pred))
            svm_acc.append(accuracy_score(y_test, svm_pred))

            nn.fit(torch.tensor(X_train.values, dtype=torch.float32), torch.tensor(y_train.values, dtype=torch.int64))
            nn_pred = nn.predict(torch.tensor(X_test.values, dtype=torch.float32))
            nn_score.append(f1_score(y_test, nn_pred))
            nn_acc.append(accuracy_score(y_test, nn_pred))

    print(f"Decision Tree F1: {np.mean(dt_score):.4f} +/- {np.std(dt_score):.4f}")
    print(f"Decision Tree Acc: {np.mean(dt_acc):.4f} +/- {np.std(dt_acc):.4f}")
    print(f"SVM F1: {np.mean(svm_score):.4f} +/- {np.std(svm_score):.4f}")
    print(f"SVM Acc: {np.mean(svm_acc):.4f} +/- {np.std(svm_acc):.4f}")
    print(f"Neural Network F1: {np.mean(nn_score):.4f} +/- {np.std(nn_score):.4f}")
    print(f"Neural Network Acc: {np.mean(nn_acc):.4f} +/- {np.std(nn_acc):.4f}")

if __name__ == "__main__":
    main()
    sys.exit(0)