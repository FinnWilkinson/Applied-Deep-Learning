import torch
import numpy as np

from sklearn import datasets
iris = datasets.load_iris()
iris.keys()

from sklearn.model_selection import train_test_split

device = torch.device('cuda')

preprocessed_features = (iris['data'] - iris['data'].mean(axis=0)) / iris['data'].std(axis=0)
labels = iris['target']
#train_test_split takes care of shuffling and splitting the data so we can have a training and testing split
train_features, test_features, train_labels, test_labels = train_test_split(preprocessed_features, labels, test_size=1/3)

features = {
    'train': torch.tensor(train_features, dtype=torch.float32),
    'test': torch.tensor(test_features, dtype=torch.float32),
}
features["train"] = features["train"].to(device)
features["test"] = features["test"].to(device)
labels = {
    'train': torch.tensor(train_labels, dtype=torch.long),
    'test': torch.tensor(test_labels, dtype=torch.long),
}
labels["train"] = labels["train"].to(device)
labels["test"] = labels["test"].to(device)

from torch import nn
from torch.nn import functional as F
from typing import Callable

class MLP(nn.Module):
  def __init__(self,
               input_size: int,
               hidden_layer_size: int,
               output_size: int,
               activation_fn: Callable[[torch.Tensor], torch.Tensor] = F.relu):
    super().__init__()
    self.l1 = nn.Linear(input_size, hidden_layer_size)
    self.l2 = nn.Linear(hidden_layer_size, output_size)
    self.activation_fn = activation_fn

  def forward(self, inputs: torch.Tensor) -> torch.Tensor:
    x = self.l1(inputs)
    x=self.activation_fn(x)
    x = self.l2(x)
    return x


feature_count = 4
hidden_layer_size = 100
class_count = 3
model = MLP(feature_count, hidden_layer_size, class_count)
model.to(device)

logits = model.forward(features['train'])
logits.shape

loss_function = nn.CrossEntropyLoss()
loss = loss_function(logits, labels['train'])
loss.backward()

def accuracy(probs: torch.FloatTensor, targets: torch.LongTensor) -> float:
  predicted_classes = torch.argmax(probs, dim=1)
  corrects = (predicted_classes == targets).sum()
  return (corrects.item() / len(targets))



from torch import optim

# Define the model to optimze
model = MLP(feature_count, hidden_layer_size, class_count)

# The optimizer we'll use to update the model parameters
optimizer = optim.SGD(model.parameters(), lr=0.05)

# Now we define the loss function.
criterion = nn.CrossEntropyLoss() 

# Now we iterate over the dataset a number of times. Each iteration of the entire dataset 
# is called an epoch.
for epoch in range(0, 100):
    # We compute the forward pass of the network
    logits = model.forward(features['train'])
    # Then the value of loss function 
    loss = criterion(logits,  labels['train'])
    
    # How well the network does on the batch is an indication of how well training is 
    # progressing
    print("epoch: {} train accuracy: {:2.2f}, loss: {:5.5f}".format(
        epoch,
        accuracy(logits, labels['train']) * 100,
        loss.item()
    ))
    
    # Now we compute the backward pass, which populates the `.grad` attributes of the parameters
    loss.backward()
    # Now we update the model parameters using those gradients
    optimizer.step()
    # Now we need to zero out the `.grad` buffers as otherwise on the next backward pass we'll add the 
    # new gradients to the old ones.
    optimizer.zero_grad()
    
# Finally we can test our model on the test set and get an unbiased estimate of its performance.    
logits = model.forward(features['test'])    
test_accuracy = accuracy(logits, labels['test']) * 100
print("test accuracy: {:2.2f}".format(test_accuracy))