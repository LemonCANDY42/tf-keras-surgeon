import sys
sys.path.append("../../")

import tensorflow as tf

from tensorflow.python.keras import layers
from tensorflow.python.keras import activations
from tensorflow.python.keras import models
from tensorflow.python.keras import backend
from tensorflow.python.keras import callbacks
from tensorflow.examples.tutorials import mnist

import tfkerassurgeon
from tfkerassurgeon import identify_by_gradient
from tfkerassurgeon.operations import delete_channels

print(tf.__version__)


# Set some static values that can be tweaked to experiment
keras_verbosity = 2 # limits the printed output but still gets the Epoch stats
epochs=200 # we'd never reach 200 because we have early stopping
batch_size=128 # tweak this depending on your hardware and Model


# Load dataset (it will automatically download it if needed)
dataset = mnist.input_data.read_data_sets('tempData', one_hot=True, reshape=False)


# Simple reusable shorthand to compile the model, so that we can be sure to use the same optomizer, loss, and metrics
def compile_model(model):
    
    model.compile(optimizer='adam',
                    loss='categorical_crossentropy',
                    metrics=['accuracy'])



# method that encapsulates the Models archeteture and construction
def build_model():

    # Create LeNet model
    model = models.Sequential()
    model.add(layers.Conv2D(20,
                     [3, 3],
                     input_shape=[28, 28, 1],
                     activation='relu',
                     name='conv_1'))
    model.add(layers.MaxPool2D())
    model.add(layers.Conv2D(50, [3, 3], activation='relu', name='conv_2'))
    model.add(layers.MaxPool2D())
    model.add(layers.Permute((2, 1, 3)))
    model.add(layers.Flatten())
    model.add(layers.Dense(500, activation='relu', name='dense_1'))
    model.add(layers.Dense(10, activation='softmax', name='dense_2'))

    compile_model(model)

    return model

# a simple method that gets the callbacks for training
def get_callbacks(use_early_stopping = True, use_reduce_lr = True):

    callback_list = []

    if(use_early_stopping):

        callback_list.append(callbacks.EarlyStopping(monitor='val_loss',
                                             min_delta=0,
                                             patience=10,
                                             verbose=keras_verbosity,
                                             mode='auto'))

    if(use_reduce_lr):

        callback_list.append(callbacks.ReduceLROnPlateau(monitor='val_loss',
                                            factor=0.1,
                                            patience=5,
                                            verbose=keras_verbosity,
                                            mode='auto',
                                            epsilon=0.0001,
                                            cooldown=0,
                                            min_lr=0))

    return callback_list

# and get the callbacks
callback_list = get_callbacks()

# Simple reusable shorthand for evaluating the model on the Validation set 
def fit_model(model):
    
    return model.fit(
                    dataset.train.images,
                    dataset.train.labels,
                    epochs=epochs,
                    batch_size=batch_size,
                    verbose=keras_verbosity,
                    validation_data=(dataset.validation.images, dataset.validation.labels),
                    callbacks=callback_list)

# Simple reusable shorthand for evaluating the model on the Validation set 
def eval_model(model):

    return model.evaluate(
                        dataset.validation.images, 
                        dataset.validation.labels, 
                        batch_size=batch_size, 
                        verbose=keras_verbosity)


# A helper that gets the layer by it's name 
def prune_layer_by_name(model, layer_name):

    # First we get the layer we are working on
    layer = model.get_layer(name=layer_name)
    # Then prune is and return the pruned model
    return prune_layer(model, layer)




# THIS IS WHERE THE MAGIC HAPPENS!
# This method uses the Keras Surgeon to identify which parts od a layer can be pruned and then deletes them
# Note: it returns the new, pruned model, that was recompiled
def prune_layer(model, layer):
    
    # Get the Output Indexes that are indicated as needing to be pruned
    prune_outputs = identify_by_gradient.get_prune_by_gradient(model, layer, datagen)

    # Run the pruning on the Model and get the Pruned (uncompiled) model as a result
    model = delete_channels(model, layer, prune_outputs)

    # Recompile the model
    compile_model(model)

    return model




# the main function, that runs the training
def main(): 

    
    # build the model
    model = build_model()

    # Initial Train on dataset
    results = fit_model(model)

    # eval and print the results of the training
    loss = eval_model(model)
    print('original model loss:', loss, '\n')
    
    # NOTE: This while true will continue until it ERRORs out because there is no escape condition.
    while True:

        # only prune the Dense layer for this example
        layer_name = 'dense_1'
        # Run the Pruning on the layer
        model = prune_layer_by_name(model, layer_name)

        # eval and print the results of the pruning
        loss = eval_model(model)
        print('model loss after pruning: ', loss, '\n')
        
        # Retrain the model to accomodate for the changes
        results = fit_model(model)

        # eval and print the results of the retraining
        loss = eval_model(model)
        print('model loss after retraining: ', loss, '\n')

        # While TRUE will repeat until an ERROR occurs


# Run the main Method
if __name__ == '__main__':
    main()

