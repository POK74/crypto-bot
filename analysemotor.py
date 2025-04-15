from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import numpy as np
import logging

logger = logging.getLogger(__name__)

class Analyzer:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            random_state=42
        )
        self.is_fitted = False

    def fit(self, X, y=None):
        try:
            # Tren scaler
            self.scaler.fit(X)
            # Tren modellen (forutsatt at vi har etiketter)
            if y is not None:
                self.model.fit(X, y)
            else:
                # Hvis ingen etiketter, bruk en enkel regelbasert tilnærming
                logger.warning("No labels provided, using default model")
            self.is_fitted = True
        except Exception as e:
            logger.error(f"Error fitting analyzer: {str(e)}")

    def analyze_data(self, data):
        try:
            # Konverter data til numpy array
            X = np.array(data)
            if not self.is_fitted:
                logger.warning("Scaler is not fitted, fitting with current data")
                self.fit(X)
            # Skaler data
            scaled_data = self.scaler.transform(X)
            # Forutsig med modellen
            prediction = self.model.predict(scaled_data)
            return prediction.tolist()
        except Exception as e:
            logger.error(f"Error in analyze_data: {str(e)}")
            return []
