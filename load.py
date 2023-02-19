from datasets import load_dataset

dataset = load_dataset("audiofolder", data_dir="dataset")
# print the first example in the training set
print(dataset["train"])