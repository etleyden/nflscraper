import torch
import torch.nn as nn
import torch.optim as optim

# Question: Is it possible to be successful with deep learning? Do we have enough data?
# TODO: comment some of these lines explaining what they do
class NN(nn.Module):
    def __init__(self, input_features, device="cpu"):
        super(NN, self).__init__()
        self.fc1 = nn.Linear(input_features, 10)
        self.fc2 = nn.Linear(10, 2)
        self.device = device
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x
    def fit(self, X, y, lr=0.01, epochs=1000):
        self.to(self.device)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.SGD(self.parameters(), lr=lr)
        for epoch in range(epochs):
            X = X.to(self.device)
            y = y.to(self.device)
            outputs = self(X)
            loss = criterion(outputs, y)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
    def predict(self, X):
        X = X.to(self.device)
        self.eval()
        y_pred = self(X)
        _, predicted = torch.max(y_pred, 1)
        return predicted.cpu().numpy()