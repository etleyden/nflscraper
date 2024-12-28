import sys
from sklearn import tree
from sklearn.svm import SVC
from sklearn.model_selection import KFold
from sklearn.metrics import f1_score
import pandas as pd
import numpy as np

def preprocess(df):
    # 1. Drop game_ids
    df.drop('game_id', axis=1, inplace=True)
    # 2. Change labels from Home | Away to -1 | 1, respectively
    df["label"] = df["label"].map({"Home": -1, "Away": 1})
    # 3. normalize columns
    data = df.drop(['label'], axis=1)
    for column in data.columns:
        data[column] = (data[column] - data[column].min()) / (data[column].max() - data[column].min())

    return data, df["label"]

def discretize(X, num_intervals=5):
    for col in X.columns:
        pd.qcut(X[col], num_intervals, labels=False)
    return X

def main():
    csv_data = pd.read_csv("nfl_2023_v1.csv")
    X, y = preprocess(csv_data)

    # models
    dt = tree.DecisionTreeClassifier()
    dt_score = []
    svm = SVC()
    svm_score = []

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
        print(y_test, svm_pred)

    print(f"Decision Tree: {np.mean(dt_score):.4f} +/- {np.std(dt_score):.4f}")
    print(f"SVM: {np.mean(svm_score):.4f} +/- {np.std(svm_score):.4f}")




if __name__ == "__main__":
    main()
    sys.exit(0)