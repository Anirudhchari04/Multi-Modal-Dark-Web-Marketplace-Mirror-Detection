"""
Ensemble Classifier - ML Model for Mirror Detection
Combines Random Forest and Gradient Boosting classifiers
"""

import numpy as np
import logging
import pickle
from typing import Tuple
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

from config import (
    RF_N_ESTIMATORS, RF_MAX_DEPTH, RF_MIN_SAMPLES_SPLIT, RF_RANDOM_STATE, RF_N_JOBS,
    GB_N_ESTIMATORS, GB_LEARNING_RATE, GB_MAX_DEPTH, GB_RANDOM_STATE, GB_SUBSAMPLE,
    TOTAL_FEATURES, PILLAR_WEIGHTS, MIRROR_THRESHOLD_HIGH, MIRROR_THRESHOLD_LOW,
    LABEL_MIRROR, LABEL_LIKELY, LABEL_NOT_MIRROR, DEFAULT_MODEL_PATH, SCALER_PATH
)


class EnsembleClassifier:
    """Ensemble ML classifier using Random Forest + Gradient Boosting."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rf_model = RandomForestClassifier(
            n_estimators=RF_N_ESTIMATORS,
            max_depth=RF_MAX_DEPTH,
            min_samples_split=RF_MIN_SAMPLES_SPLIT,
            random_state=RF_RANDOM_STATE,
            n_jobs=RF_N_JOBS
        )
        self.gb_model = GradientBoostingClassifier(
            n_estimators=GB_N_ESTIMATORS,
            learning_rate=GB_LEARNING_RATE,
            max_depth=GB_MAX_DEPTH,
            random_state=GB_RANDOM_STATE,
            subsample=GB_SUBSAMPLE
        )
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> float:
        """Train the ensemble models."""
        try:
            self.logger.info(f"Training ensemble on {len(X_train)} samples")
            
            # Normalize features
            X_normalized = self.scaler.fit_transform(X_train)
            
            # Train models
            self.rf_model.fit(X_normalized, y_train)
            self.gb_model.fit(X_normalized, y_train)
            
            self.is_trained = True
            
            # Calculate training accuracy
            rf_accuracy = self.rf_model.score(X_normalized, y_train)
            gb_accuracy = self.gb_model.score(X_normalized, y_train)
            ensemble_accuracy = (rf_accuracy + gb_accuracy) / 2
            
            self.logger.info(f"RF Accuracy: {rf_accuracy:.4f}")
            self.logger.info(f"GB Accuracy: {gb_accuracy:.4f}")
            self.logger.info(f"Ensemble Accuracy: {ensemble_accuracy:.4f}")
            
            return ensemble_accuracy
            
        except Exception as e:
            self.logger.error(f"Error training models: {e}")
            return 0.0
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probability of being a mirror."""
        try:
            if not self.is_trained:
                self.logger.warning("Models not trained yet")
                return np.zeros(len(X))
            
            # Normalize features
            X_normalized = self.scaler.transform(X)
            
            # Get predictions from both models
            rf_proba = self.rf_model.predict_proba(X_normalized)[:, 1]
            gb_proba = self.gb_model.predict_proba(X_normalized)[:, 1]
            
            # Average predictions
            ensemble_proba = (rf_proba + gb_proba) / 2
            
            return ensemble_proba
            
        except Exception as e:
            self.logger.error(f"Error predicting probabilities: {e}")
            return np.zeros(len(X))
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict classification and get probabilities."""
        try:
            probabilities = self.predict_proba(X)
            predictions = (probabilities > MIRROR_THRESHOLD_HIGH).astype(int)
            return predictions, probabilities
            
        except Exception as e:
            self.logger.error(f"Error making predictions: {e}")
            return np.zeros(len(X)), np.zeros(len(X))
    
    def save_model(self, file_path: str) -> bool:
        """Save trained models to file."""
        try:
            model_data = {
                'rf_model': self.rf_model,
                'gb_model': self.gb_model,
                'scaler': self.scaler,
                'is_trained': self.is_trained
            }
            with open(file_path, 'wb') as f:
                pickle.dump(model_data, f)
            self.logger.info(f"Models saved to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving models: {e}")
            return False
    
    def load_model(self, file_path: str) -> bool:
        """Load trained models from file."""
        try:
            with open(file_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.rf_model = model_data['rf_model']
            self.gb_model = model_data['gb_model']
            self.scaler = model_data['scaler']
            self.is_trained = model_data.get('is_trained', True)
            
            self.logger.info(f"Models loaded from {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
            return False


class MirrorDetectionPipeline:
    """Complete pipeline for mirror detection."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.classifier = EnsembleClassifier()
        self.detection_info = {}
    
    def combine_pillar_features(self, pillar_features: dict) -> np.ndarray:
        """Combine features from all 7 pillars with weights."""
        try:
            combined = []
            
            # Collect all features in order
            for i in range(1, 8):
                pillar_name = f"pillar_{i}"
                if pillar_name in pillar_features:
                    features = pillar_features[pillar_name]
                    if isinstance(features, np.ndarray):
                        combined.extend(features)
            
            if not combined:
                self.logger.error("No features collected")
                return np.zeros(TOTAL_FEATURES)
            
            combined_array = np.array(combined[:TOTAL_FEATURES])
            
            # Pad with zeros if necessary
            if len(combined_array) < TOTAL_FEATURES:
                combined_array = np.pad(combined_array, (0, TOTAL_FEATURES - len(combined_array)))
            
            # Normalize to valid range
            combined_array = np.clip(combined_array, 0, 1)
            
            return combined_array
            
        except Exception as e:
            self.logger.error(f"Error combining features: {e}")
            return np.zeros(TOTAL_FEATURES)
    
    def generate_classification(self, probability: float) -> str:
        """Generate classification label from probability."""
        if probability > MIRROR_THRESHOLD_HIGH:
            return LABEL_MIRROR
        elif probability > MIRROR_THRESHOLD_LOW:
            return LABEL_LIKELY
        else:
            return LABEL_NOT_MIRROR
    
    def _generate_summary(self, old_url: str, new_url: str, score: float, classification: str, pillar_scores: dict) -> str:
        """Generate human-readable summary."""
        summary = f"""
DARKNET MARKETPLACE MIRROR DETECTION REPORT
============================================
Old Marketplace: {old_url}
New Marketplace: {new_url}

Final Mirror Score: {score:.2%}
Classification: {classification}
Confidence: {int(score * 100)}%

Pillar Analysis Scores:
  HTTP Response Fingerprinting:    {pillar_scores.get('pillar_1', 0.0):.2%}
  HTML/DOM Structure Analysis:     {pillar_scores.get('pillar_2', 0.0):.2%}
  JavaScript Code Analysis:        {pillar_scores.get('pillar_3', 0.0):.2%}
  PGP Cryptographic Verification:  {pillar_scores.get('pillar_4', 0.0):.2%} (HIGHEST WEIGHT)
  Exception Handling Patterns:     {pillar_scores.get('pillar_5', 0.0):.2%}
  Response Timing Analysis:        {pillar_scores.get('pillar_6', 0.0):.2%}
  API Endpoint Analysis:           {pillar_scores.get('pillar_7', 0.0):.2%}

Recommendation:
"""
        if classification == LABEL_MIRROR:
            summary += "  ⚠️  HIGH CONFIDENCE MIRROR DETECTED - IMMEDIATE LAW ENFORCEMENT ACTION RECOMMENDED"
        elif classification == LABEL_LIKELY:
            summary += "  ⚠️  LIKELY MIRROR - MANUAL INVESTIGATION RECOMMENDED"
        else:
            summary += "  ✓  No mirror detected - No action required"
        
        summary += "\n============================================\n"
        return summary
    
    def detect_mirror(self, combined_features: np.ndarray, old_url: str, new_url: str, pillar_scores: dict = None) -> dict:
        """Complete mirror detection pipeline."""
        try:
            # Reshape for model input
            X = combined_features.reshape(1, -1)
            
            # Get prediction
            probability = self.classifier.predict_proba(X)[0]
            classification = self.generate_classification(probability)
            
            # Generate output
            result = {
                "old_marketplace": old_url,
                "new_marketplace": new_url,
                "final_mirror_score": float(probability),
                "classification": classification,
                "confidence_percentage": int(probability * 100),
                "pillar_scores": pillar_scores or {},
                "summary": self._generate_summary(old_url, new_url, probability, classification, pillar_scores or {}),
                "recommendation": "INVESTIGATE" if probability > MIRROR_THRESHOLD_LOW else "NO ACTION",
                "extraction_info": {
                    "total_features_extracted": TOTAL_FEATURES,
                    "model_type": "Ensemble (RF + GB)",
                    "status": "success"
                }
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in detection pipeline: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }


def create_ensemble_model() -> EnsembleClassifier:
    """Create and return an ensemble classifier instance."""
    return EnsembleClassifier()


def create_detection_pipeline() -> MirrorDetectionPipeline:
    """Create and return a detection pipeline instance."""
    return MirrorDetectionPipeline()
