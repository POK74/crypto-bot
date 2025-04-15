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
            # Tren scaler med data
            self.scaler.fit(X)
            # Tren modellen hvis etiketter er gitt
            if y is not None:
                scaled_X = self.scaler.transform(X)
                self.model.fit(scaled_X, y)
            else:
                logger.warning("No labels provided, using default model")
            self.is_fitted = True
            logger.info("Analyzer successfully fitted")
        except Exception as e:
            logger.error(f"Error fitting analyzer: {str(e)}")
            raise

    def analyze_data(self, data):
        try:
            if not self.is_fitted:
                raise ValueError("Analyzer is not fitted. Call 'fit' with training data first.")
            # Konverter data til numpy array
            X = np.array(data)
            # Skaler data
            scaled_data = self.scaler.transform(X)
            # Forutsig med modellen
            prediction = self.model.predict(scaled_data)
            return prediction.tolist()
        except Exception as e:
            logger.error(f"Error in analyze_data: {str(e)}")
            raise
