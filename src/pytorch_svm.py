# exploring using a pytorch of an SVM for GPU offloading
# result: unsuccessful (all predictions are 1)
import sys 

from train_model import preprocess
import pandas as pd
from sklearn.model_selection import KFold

import torch
import torch.nn as nn
import torch.optim as optim

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def hinge_loss(output, target):
    return torch.mean(torch.clamp(1 - output * target, min=0))

class SVM(nn.Module):
    def __init__(self, input_dim, device="cpu"):
        super(SVM, self).__init__()
        self.device = device
        self.linear = nn.Linear(input_dim, 1)

    def forward(self, x):
        return self.linear(x)

    def fit(self, X, y, lr=0.01, epochs=100):
        optimizer = optim.SGD(self.parameters(), lr=lr)
        for epoch in range(epochs):
            self.train()

            # forward pass
            outputs = self(X).squeeze()
            loss = hinge_loss(outputs, y)

            # backward pass and optimization
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            if (epoch + 1) % 10 == 0:
                print(f'Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}')
    
    def predict(self, X):
        self.eval()
        with torch.no_grad():
            outputs = self(X).squeeze()
            y_pred = torch.sign(outputs)
            return y_pred

def main():
    if len(sys.argv) > 1:
        fpath = sys.argv[1]
    else:
        print("Usage: python train_model.py [train.csv]")
        sys.exit(1)
    csv_data = pd.read_csv(fpath)
    X, y = preprocess(csv_data)

    svm = SVM(len(X.columns), device=device)

    kf = KFold(n_splits=5, shuffle=True)

    for i, (train_idx, test_idx) in enumerate(kf.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        svm.fit(torch.tensor(X_train.values, dtype=torch.float32), torch.tensor(y_train.values, dtype=torch.float32))
        pred = svm.predict(torch.tensor(X_test.values, dtype=torch.float32))
        print(pred)
        print()


if __name__ == "__main__":
    main()
    sys.exit(0)