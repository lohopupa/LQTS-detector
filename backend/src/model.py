
from tensorflow.keras.models import load_model
import pandas as pd
import numpy as np
import os

class Model:
    def __init__(self):
        modelPath = os.path.join('models', 'fold.h5')
        self.model = load_model(modelPath)
        
    def predict(self, data):
        return (self.model.predict(data)>0.5).astype("int32")[0]
    
def load_model_split():
    return load_model(os.path.join('models', 'best_model.keras'))