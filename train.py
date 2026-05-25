"""
Training Script for Mirror Detection Model
Generates synthetic data and trains the ensemble classifier
"""

import numpy as np
import pandas as pd
import logging
import argparse
import sys
import os

from config import (
    TOTAL_FEATURES, MIN_TRAINING_SAMPLES, TRAINING_TEST_SIZE,
    TRAINING_RANDOM_STATE, LOG_LEVEL, DEFAULT_MODEL_PATH
)
from utils import LoggingSetup
from ensemble_classifier import EnsembleClassifier


def generate_synthetic_training_data(num_mirrors: int = 100, num_non_mirrors: int = 100) -> tuple:
    """Generate synthetic training data."""
    logger = LoggingSetup.setup_logging("data_generator", LOG_LEVEL)
    logger.info(f"Generating synthetic data: {num_mirrors} mirrors, {num_non_mirrors} non-mirrors")
    
    X = []
    y = []
    
    # Generate mirror samples (high feature values, closer to 1)
    for _ in range(num_mirrors):
        # Mirrors have high similarity across all features
        features = np.random.uniform(0.6, 1.0, TOTAL_FEATURES)
        X.append(features)
        y.append(1)
    
    # Generate non-mirror samples (low feature values, closer to 0)
    for _ in range(num_non_mirrors):
        # Non-mirrors have low similarity across features
        features = np.random.uniform(0.0, 0.4, TOTAL_FEATURES)
        X.append(features)
        y.append(0)
    
    X = np.array(X)
    y = np.array(y)
    
    # Shuffle
    shuffle_idx = np.random.permutation(len(X))
    X = X[shuffle_idx]
    y = y[shuffle_idx]
    
    logger.info(f"Generated {len(X)} training samples with {TOTAL_FEATURES} features")
    return X, y


def load_training_data(csv_path: str) -> tuple:
    """Load training data from CSV file."""
    logger = LoggingSetup.setup_logging("data_loader", LOG_LEVEL)
    
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded data from {csv_path}")
        
        # Assume last column is label
        X = df.iloc[:, :-1].values
        y = df.iloc[:, -1].values
        
        logger.info(f"Loaded {len(X)} samples with {X.shape[1]} features")
        return X, y
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return None, None


def train_model(X_train: np.ndarray, y_train: np.ndarray, output_path: str = DEFAULT_MODEL_PATH) -> bool:
    """Train the ensemble model."""
    logger = LoggingSetup.setup_logging("trainer", LOG_LEVEL)
    
    try:
        # Create and train classifier
        classifier = EnsembleClassifier()
        accuracy = classifier.train(X_train, y_train)
        
        logger.info(f"Model trained with accuracy: {accuracy:.4f}")
        
        # Save model
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        success = classifier.save_model(output_path)
        
        if success:
            logger.info(f"Model saved to {output_path}")
            return True
        else:
            logger.error("Failed to save model")
            return False
            
    except Exception as e:
        logger.error(f"Error training model: {e}")
        return False


def main():
    """Main training script."""
    parser = argparse.ArgumentParser(description="Train Mirror Detection Model")
    parser.add_argument("--data", help="Path to training data CSV", default=None)
    parser.add_argument("--output", help="Output model path", default=DEFAULT_MODEL_PATH)
    parser.add_argument("--mirrors", type=int, default=100, help="Number of synthetic mirror samples")
    parser.add_argument("--non-mirrors", type=int, default=100, help="Number of synthetic non-mirror samples")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    logger = LoggingSetup.setup_logging("train", LOG_LEVEL if args.verbose else logging.INFO)
    
    logger.info("Starting model training...")
    
    # Load or generate data
    if args.data:
        logger.info(f"Loading training data from {args.data}")
        X, y = load_training_data(args.data)
        if X is None:
            logger.error("Failed to load training data")
            sys.exit(1)
    else:
        logger.info("Generating synthetic training data")
        X, y = generate_synthetic_training_data(args.mirrors, args.non_mirrors)
    
    # Validate data
    if len(X) < MIN_TRAINING_SAMPLES:
        logger.error(f"Insufficient training samples: {len(X)} < {MIN_TRAINING_SAMPLES}")
        sys.exit(1)
    
    if X.shape[1] != TOTAL_FEATURES:
        logger.error(f"Feature mismatch: {X.shape[1]} != {TOTAL_FEATURES}")
        sys.exit(1)
    
    # Train model
    logger.info(f"Training with {len(X)} samples, {X.shape[1]} features")
    success = train_model(X, y, args.output)
    
    if success:
        logger.info("Training completed successfully")
        sys.exit(0)
    else:
        logger.error("Training failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
