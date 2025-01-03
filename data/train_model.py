import sys
import pandas as pd
import numpy as np

from sklearn import tree
from sklearn.svm import SVC
from sklearn.model_selection import KFold
from sklearn.metrics import f1_score

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
    # 3. normalize columns
    data = df.drop(['label'], axis=1)
    for column in data.columns:
        data[column] = (data[column] - data[column].min()) / (data[column].max() - data[column].min())

    return data, df["label"]

class CustomNN(nn.Module):
    def __init__(self, input_features):
        super(CustomNN, self).__init__()
        self.fc1 = nn.Linear(input_features, 10)
        self.fc2 = nn.Linear(10, 2)
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x
    def fit(self, X, y, lr=0.01, epochs=1000):
        self.to(device)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.SGD(self.parameters(), lr=lr)
        for epoch in range(epochs):
            X = X.to(device)
            y = y.to(device)
            outputs = self(X)
            loss = criterion(outputs, y)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
    def predict(self, X):
        X = X.to(device)
        self.eval()
        y_pred = self(X)
        _, predicted = torch.max(y_pred, 1)
        return predicted.cpu().numpy()

def main():
    csv_data = pd.read_csv("nfl_2023_v1.csv")
    X, y = preprocess(csv_data)

    # models
    dt, dt_score = tree.DecisionTreeClassifier(), []
    svm, svm_score = SVC(), []
    nn, nn_score = CustomNN(5), []

    # five fold cross validation
    kf = KFold(n_splits=5, shuffle=True)
    for i, (train_idx, test_idx) in enumerate(kf.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        dt.fit(X_train, y_train)
        dt_pred = dt.predict(X_test)
        dt_score.append(f1_score(y_test, dt_pred))

        svm.fit(X_train, y_train)
        svm_pred = svm.predict(X_test)
        svm_score.append(f1_score(y_test, svm_pred))

        nn.fit(torch.tensor(X_train.values, dtype=torch.float32), torch.tensor(y_train.values, dtype=torch.int64))
        nn_pred = nn.predict(torch.tensor(X_test.values, dtype=torch.float32))
        print(y_test.values, nn_pred)
        nn_score.append(f1_score(y_test, nn_pred))

    print(f"Decision Tree: {np.mean(dt_score):.4f} +/- {np.std(dt_score):.4f}")
    print(f"SVM: {np.mean(svm_score):.4f} +/- {np.std(svm_score):.4f}")
    print(f"Neural Network: {np.mean(nn_score):.4f} +/- {np.std(nn_score):.4f}")

if __name__ == "__main__":
    main()
    sys.exit(0)