import sys
import pandas as pd
from tqdm import tqdm
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import f1_score
import train_model #preprocess method

def main():
    csv_data = pd.read_csv("nfl.csv")
    X, y = train_model.preprocess(csv_data)
    #TODO: answer the question: will increasing the amount of data change the optimal parameters?
    svm_params = {
        "C": [0.001, 0.01, 0.1, 1, 10, 100], 
        "gamma": [0.001, 0.01, 0.1, 1, 10, 100],  # all kernels except linear
        "kernel": ["linear", "poly", "rbf", "sigmoid"],
        "degree": [2, 3, 4, 5] # only poly
    }
    num_configurations = 1;
    for param in svm_params:
        num_configurations *= len(svm_params[param])
    print(f"Total Configurations: {num_configurations}")
    svm, svm_score, svm_acc = SVC(), [], []
    # GridSearch automatically does 5 fold cross validation
    svm = GridSearchCV(svm, svm_params, n_jobs=-1, scoring="f1", verbose=2)
        
    svm.fit(X, y)

    print(svm.get_params())
    

if __name__ == "__main__":
    main()
    sys.exit()

