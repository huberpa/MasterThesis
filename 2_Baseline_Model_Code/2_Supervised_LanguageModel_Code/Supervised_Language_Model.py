
# Commandline Arguments
##############################################
import optparse
parser = optparse.OptionParser()
parser.add_option('--dataset', action="store", dest="dataset", help="Choose the dataset to train on [PRD,DEV] (default: PRD)", default="PRD")
parser.add_option('--layers', action="store", dest="layers", help="The number of hidden layers in the model (default: 1)", default=1)
parser.add_option('--layer_dim', action="store", dest="layer_dim", help="The number of neurons in the hidden layer(s)  (default: 512)", default=512)
parser.add_option('--embedding_dim', action="store", dest="embedding_dim", help="The number of dimensions the embedding has  (default: 256)", default=256)
parser.add_option('--batch_size', action="store", dest="batch_size", help="The batch size of the model (default: 100)", default=100)
parser.add_option('--epochs', action="store", dest="epochs", help="The number of training epochs (default: 25)", default=25)
parser.add_option('--vocabulary_size', action="store", dest="vocabulary_size", help="Size of the vocabulary (default: 30000)", default=30000)
parser.add_option('--unknown_token', action="store", dest="unknown_token", help="Token for words that are not in the vacabulary (default: <UNKWN>)", default="<UNKWN>")
parser.add_option('--start_token', action="store", dest="start_token", help="Token for start (default: <START>)", default="<START>")
parser.add_option('--end_token', action="store", dest="end_token", help="Token for end (default: <END>)", default="<END>")
parser.add_option('--save_path', action="store", dest="save_path", help="The path to save the folders (logging, models etc.)  (default: .)", default=".")
parser.add_option('--continue_version', action="store", dest="continue_version", help="Continue to learn a already started model (default: 0)", default=0)
parser.add_option('--starting_epoch', action="store", dest="starting_epoch", help="Continue learning with this epoch (default: 1)", default=1)
parser.add_option('--lr', action="store", dest="lr", help="Learning rate (default: 1e-3)", default="1e-3")
options, args = parser.parse_args()
nb_hidden_layers = int(options.layers)
hidden_dimensions= int(options.layer_dim)
embedding_size = int(options.embedding_dim)
batch_size = int(options.batch_size)
trainingIterations = int(options.epochs)
starting_epoch = int(options.starting_epoch)
continue_version = int(options.continue_version)
continue_learning = 0
if(int(starting_epoch) > 1):
    continue_learning = 1
path_to_folders = options.save_path
vocabulary_size = int(options.vocabulary_size)
unknown_token = options.unknown_token
start_token = options.start_token
end_token = options.end_token
learning_rate = float(options.lr)
dataset = options.dataset
if dataset == "DEV":
    training_data = "./../tedData/sets/development/indicated_development_texts.txt"
if dataset == "PRD":
    training_data = "./../tedData/sets/training/indicated_training_texts.txt"
##############################################



# Imports
##############################################
from keras.models import Sequential, load_model
from keras.layers import Dense, Activation, Embedding, LSTM
from keras.preprocessing import sequence as kerasSequence
from keras.layers.wrappers import TimeDistributed
from collections import Counter
from keras import optimizers
import numpy as np
import random
import sys
import nltk
import re
import os
import datetime
import json
import copy
##############################################



# Main
##############################################

# Open the training dataset
print "Reading training data..."
path  = open(training_data, "r")
text = path.read().decode('utf8')

# Split the text in sentences and words --> tokens[#sentence][#word]
print "Tokenizing file..."
words = nltk.word_tokenize(text)
for index, word in enumerate(words):
    if word.find("___") > -1:
        words[index] = word[word.find("___")+3:word.rfind("___")]
words = [word.lower() for word in words]

tokens = []
classToken = []
for index, sentence in enumerate(nltk.sent_tokenize(text)): 
    tokens.append(nltk.word_tokenize(sentence))


for index, sentence in enumerate(tokens):
    classToken.append([])
    for index2, word in enumerate(sentence):
        classToken[index].append(0)
        if word.find("___") > -1:
            classToken[index][index2] = 1
            tokens[index][index2] = word[word.find("___")+3:word.rfind("___")]
tokens = [[word.lower() for word in sentence] for sentence in tokens]

# All words that occur in the text and cut the first vocabulary_size
print "Creating vocabulary..."
allVocab = [word[0] for word in Counter(words).most_common()]
vocab = ["<PAD>"]+allVocab[:vocabulary_size]
vocab.append(unknown_token)
vocab.append(start_token)
vocab.append(end_token)

# Mapping from word to Index and vice versa
print "Creating mappings..."
index_to_word = dict((index, word) for index, word in enumerate(vocab))
word_to_index = dict((word, index) for index, word in enumerate(vocab))

# Adding the unknown_token and transforming the text into indexes
print "Creating integer array..."
for index1, sentence in enumerate(tokens):
    for index2, word in enumerate(sentence):
        tokens[index1][index2] = word_to_index[word] if word in word_to_index else word_to_index[unknown_token]

# Adding the start- and end-tokens to the sentences
print "Adding start and end tokens..."
for index, sentence in enumerate(tokens):
    tokens[index] = [word_to_index[start_token]] + tokens[index] + [word_to_index[end_token]]
    classToken[index] = [0] + classToken[index] + [0]



# Cut all sentences that are longer than 50 words
longestSentence = 50
for index, sentence in enumerate(tokens):
    if len(sentence) > longestSentence:
        tokens[index] = tokens[index][:longestSentence]

# Split the sentences into input and output by shifting them by one
input_Words = []
output_Words = []
for index, sentence in enumerate(tokens):
    input_Words.append(sentence)
    output_Words.append(classToken[index])

# Pad the sequences with zeros
print "Padding sequences with zeros..."
pad_input_Words = kerasSequence.pad_sequences(input_Words, maxlen=longestSentence, padding='pre', value=0)
pad_output_Words = kerasSequence.pad_sequences(output_Words, maxlen=longestSentence, padding='pre', value=0)

# Print information
print 'Finished initialization with......'
print 'Number of sequences:' + str(len(input_Words))
print 'Number of words (vocabulary):' + str(len(vocab)) + " (full vocabulary consists of " + str(len(allVocab)) + " unique words)"
print 'Length of Input (Longest sentence):' + str(longestSentence)

# Create NUMPY arrays to enter the data into the network
print('Vectorization...')
trainingInput = np.zeros((len(pad_input_Words), longestSentence), dtype=np.int16)
trainingOutput = np.zeros((len(pad_output_Words), longestSentence), dtype=np.int16)

# Copy the lists into NUMPY arrays
for index1, sequence in enumerate(pad_input_Words):
    for index2, word in enumerate(sequence):
        trainingInput[index1, index2] = word

for index1, sequence in enumerate(pad_output_Words):
    for index2, word in enumerate(sequence):        
        trainingOutput[index1, index2] = word


print ("-"*50)
zip1 = []
zip2 = []
for i in range(0,20):
    for index, val in enumerate(trainingInput[i]):
        zip1.append(index_to_word[val])
        zip2.append(trainingOutput[i][index])
    print zip(zip1, zip2)
    print ("-"*50)

trainingOutput = np.expand_dims(trainingOutput, -1)

# Check if an existing model should be extended or if a new model should be created
if continue_learning == 1:
    # Load the model
    print('Load the Model...')
    idx = continue_version
    model = load_model(path_to_folders + "/models_" + str(idx) + "/LM_model_Iteration_" + str(starting_epoch-1) + ".h5")

else:
    idx = 1
    loop = 1
    while loop:
        if not os.path.exists(path_to_folders + "/files_"+str(idx)):
            os.makedirs(path_to_folders + "/files_"+str(idx))
            with open(path_to_folders + "/files_"+str(idx)+"/index_to_word.json", "w") as f:
                json.dump(index_to_word, f)
            with open(path_to_folders + "/files_"+str(idx)+"/word_to_index.json", "w") as f:
                json.dump(word_to_index, f)
        if not os.path.exists(path_to_folders + "/log_"+str(idx)):
            os.makedirs(path_to_folders + "/log_"+str(idx))
            logFile = open(path_to_folders + "/log_"+str(idx)+"/logging.log","a")
            logFile.close()
        if not os.path.exists(path_to_folders + "/models_"+str(idx)):
            os.makedirs(path_to_folders + "/models_"+str(idx))
            loop = 0
        if loop == 1:
            idx += 1

    # Build the model
    print('Building the Model...')
    model = Sequential()
    model.add(Embedding(input_dim=len(vocab), output_dim=embedding_size, mask_zero=True))
    for layer in range(0, nb_hidden_layers):
        print "add LSTM layer...."
        model.add(LSTM(units=hidden_dimensions, return_sequences=True))
    model.add(TimeDistributed(Dense(1, activation='sigmoid')))
    optimizer = optimizers.Adam(lr=learning_rate)

    model.compile(loss='binary_crossentropy', optimizer=optimizer)

# Output the networks architecture
print model.summary() 

# Iterate trough the trainingsset
for iteration in range(starting_epoch, starting_epoch+trainingIterations):

    # Stdout formatting
    print ""
    print('#' * 50)
    print ""
    print'Iteration: ' + str(iteration)

    # Fitting the data into the model
    iterationResult = model.fit(trainingInput, trainingOutput, batch_size=int(batch_size), epochs=1)

    # Log the iteration results
    with open(path_to_folders + "/log_" + str(idx) + "/logging.log", "a") as logFile:
        if iteration == 1:
            logFile.write("{}\n".format(options))

        logData = training_data
        logDate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logIteration = " --- Iteration: " + str(iteration)
        logLoss = " --- Loss: " + str(iterationResult.history.get('loss')[0])
    
        logFile.write("{}\n".format(""))
        logFile.write("{}\n".format(logData + " --- " + logDate+logIteration+logLoss))
        logFile.write("{}\n".format(""))
        logFile.write("{}\n".format("+"*50))

    # Save the model at the end of the iteration
    model.save(path_to_folders + "/models_" + str(idx) + "/LM_model_Iteration_" + str(iteration) + '.h5')

