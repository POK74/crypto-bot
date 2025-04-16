import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import logging

logger = logging.getLogger(__name__)

class Analyzer:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)

    def fit(self, data):
        try:
            # Velg kun numeriske kolonner for skalering og trening
            X = data[['close', 'volume']].copy()  # Ekskluder 'timestamp' og andre ikke-numeriske kolonner
            y = data['label']

            # Skaler funksjonene
            X_scaled = self.scaler.fit_transform(X)
            
            # Tren modellen
            self.model.fit(X_scaled, y)
            logger.info("Analyzer successfully fitted")
        except Exception as e:
            logger.error(f"Error fitting analyzer: {str(e)}")
            raise

    def predict(self, features):
        try:
            # Velg kun numeriske kolonner for prediksjon
            X = features[['close', 'volume']].copy()
            
            # Skaler funksjonene
            X_scaled = self.scaler.transform(X)
            
            # Gjør prediksjon
            prediction = self.model.predict(X_scaled)
            return prediction
        except Exception as e:
            logger.error(f"Error predicting with analyzer: {str(e)}")
            return [0]  # Fallback-prediksjon
