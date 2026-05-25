"""
Examples - 7 Practical Usage Examples for Mirror Detection System
Demonstrates each pillar and the complete pipeline
"""

import numpy as np
import logging
from config import LOG_LEVEL, HTTP_TIMEOUT
from utils import LoggingSetup

# Setup logging
logger = LoggingSetup.setup_logging("examples", LOG_LEVEL)


def example_1_single_pillar_extraction():
    """Example 1: Extract features from Pillar 1 (HTTP Response Fingerprinting)."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Single Pillar Extraction (HTTP Fingerprinting)")
    print("="*60)
    
    try:
        from pillar_1_http import extract_http_features
        
        # Example marketplace URLs (these would be real Tor addresses)
        old_url = "http://marketplace1.onion"
        new_url = "http://marketplace2.onion"
        
        logger.info(f"Extracting HTTP features from: {old_url} and {new_url}")
        
        # Extract features
        http_features = extract_http_features(old_url, new_url, timeout=HTTP_TIMEOUT)
        
        print(f"\nHTTP Features Shape: {http_features.shape}")
        print(f"HTTP Features (12): {http_features}")
        print(f"Mean HTTP Score: {np.mean(http_features):.4f}")
        
        return http_features
        
    except Exception as e:
        logger.error(f"Error in Example 1: {e}")
        return np.zeros(12)


def example_2_html_analysis():
    """Example 2: Extract HTML/DOM structure features."""
    print("\n" + "="*60)
    print("EXAMPLE 2: HTML/DOM Structure Analysis")
    print("="*60)
    
    try:
        from pillar_2_html import extract_html_features
        
        old_url = "http://marketplace1.onion"
        new_url = "http://marketplace2.onion"
        
        logger.info(f"Extracting HTML features from: {old_url} and {new_url}")
        
        html_features = extract_html_features(old_url, new_url, timeout=HTTP_TIMEOUT)
        
        print(f"\nHTML Features Shape: {html_features.shape}")
        print(f"HTML Features (15): {html_features}")
        print(f"Mean HTML Score: {np.mean(html_features):.4f}")
        
        # Identify key metrics
        dom_depth_sim = html_features[2]
        tag_jaccard = html_features[6]
        css_jaccard = html_features[7]
        
        print(f"\nKey Metrics:")
        print(f"  DOM Depth Similarity: {dom_depth_sim:.4f}")
        print(f"  Tag Frequency Jaccard: {tag_jaccard:.4f}")
        print(f"  CSS Classes Jaccard: {css_jaccard:.4f}")
        
        return html_features
        
    except Exception as e:
        logger.error(f"Error in Example 2: {e}")
        return np.zeros(15)


def example_3_pgp_analysis():
    """Example 3: PGP cryptographic verification."""
    print("\n" + "="*60)
    print("EXAMPLE 3: PGP Cryptographic Verification")
    print("="*60)
    
    try:
        from pillar_4_pgp import extract_pgp_features
        
        # Example PGP fingerprints (40-char or 64-char hex strings)
        old_fingerprints = [
            "1234567890ABCDEF1234567890ABCDEF12345678",  # 40-char
            "1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF"  # 64-char
        ]
        
        new_fingerprints = [
            "1234567890ABCDEF1234567890ABCDEF12345678",  # Exact match
            "9876543210FEDCBA9876543210FEDCBA98765432"   # Different
        ]
        
        logger.info("Extracting PGP features")
        
        pgp_features = extract_pgp_features(old_fingerprints, new_fingerprints)
        
        print(f"\nPGP Features Shape: {pgp_features.shape}")
        print(f"PGP Features (12): {pgp_features}")
        print(f"Mean PGP Score: {np.mean(pgp_features):.4f}")
        
        print(f"\nKey Metrics:")
        print(f"  Exact Fingerprint Match: {pgp_features[0]:.4f}")
        print(f"  Partial Overlap (last 16 chars): {pgp_features[1]:.4f}")
        print(f"  Jaccard Similarity: {pgp_features[2]:.4f}")
        print(f"  Average Fingerprint Similarity: {pgp_features[7]:.4f}")
        
        return pgp_features
        
    except Exception as e:
        logger.error(f"Error in Example 3: {e}")
        return np.zeros(12)


def example_4_training_classifier():
    """Example 4: Train a new classifier model."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Training Classifier Model")
    print("="*60)
    
    try:
        import numpy as np
        from ensemble_classifier import EnsembleClassifier
        from config import TOTAL_FEATURES
        
        # Generate synthetic training data
        np.random.seed(42)
        
        # Mirrors (high feature values)
        X_mirrors = np.random.uniform(0.6, 1.0, (100, TOTAL_FEATURES))
        
        # Non-mirrors (low feature values)
        X_non_mirrors = np.random.uniform(0.0, 0.4, (100, TOTAL_FEATURES))
        
        # Combine
        X_train = np.vstack([X_mirrors, X_non_mirrors])
        y_train = np.hstack([np.ones(100), np.zeros(100)])
        
        # Shuffle
        idx = np.random.permutation(len(X_train))
        X_train = X_train[idx]
        y_train = y_train[idx]
        
        logger.info(f"Training on {len(X_train)} samples")
        
        # Train classifier
        classifier = EnsembleClassifier()
        accuracy = classifier.train(X_train, y_train)
        
        print(f"\nTraining Complete!")
        print(f"Ensemble Accuracy: {accuracy:.4f}")
        
        # Make some predictions
        test_samples = np.random.uniform(0.5, 0.8, (5, TOTAL_FEATURES))
        predictions, probabilities = classifier.predict(test_samples)
        
        print(f"\nTest Predictions:")
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            label = "MIRROR" if pred == 1 else "NOT MIRROR"
            print(f"  Sample {i+1}: {label} (confidence: {prob:.2%})")
        
        return classifier
        
    except Exception as e:
        logger.error(f"Error in Example 4: {e}")
        return None


def example_5_inference_pipeline():
    """Example 5: Complete detection pipeline."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Complete Detection Pipeline")
    print("="*60)
    
    try:
        from main import MarketplaceMirrorDetector
        import json
        
        # Example URLs
        old_url = "http://marketplace1.onion"
        new_url = "http://marketplace2.onion"
        
        logger.info("Running complete detection pipeline")
        
        # Create detector
        detector = MarketplaceMirrorDetector()
        
        # Run detection
        result = detector.detect_mirror(old_url, new_url)
        
        print(f"\nDetection Results:")
        print(json.dumps(result, indent=2))
        
        if "summary" in result:
            print(result["summary"])
        
        return result
        
    except Exception as e:
        logger.error(f"Error in Example 5: {e}")
        return None


def example_6_custom_weights():
    """Example 6: Using custom pillar weights."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Custom Pillar Weights")
    print("="*60)
    
    try:
        from config import PILLAR_WEIGHTS
        
        print(f"\nDefault Pillar Weights:")
        for pillar, weight in PILLAR_WEIGHTS.items():
            print(f"  {pillar}: {weight:.2f}")
        
        print(f"\nSum of weights: {sum(PILLAR_WEIGHTS.values()):.2f}")
        
        # Example: Increase PGP weight
        custom_weights = PILLAR_WEIGHTS.copy()
        custom_weights["pillar_4_pgp"] = 0.35  # Increase from 0.25
        custom_weights["pillar_1_http"] = 0.10  # Decrease from 0.15
        
        print(f"\nCustom Weights (emphasize PGP):")
        for pillar, weight in custom_weights.items():
            print(f"  {pillar}: {weight:.2f}")
        
        print(f"Sum of custom weights: {sum(custom_weights.values()):.2f}")
        
        return custom_weights
        
    except Exception as e:
        logger.error(f"Error in Example 6: {e}")
        return None


def example_7_batch_processing():
    """Example 7: Batch processing multiple marketplace pairs."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Batch Processing Multiple Pairs")
    print("="*60)
    
    try:
        from main import MarketplaceMirrorDetector
        import json
        
        # List of marketplace pairs to analyze
        marketplace_pairs = [
            ("http://market1.onion", "http://mirror1.onion"),
            ("http://market2.onion", "http://mirror2.onion"),
            ("http://market3.onion", "http://mirror3.onion"),
        ]
        
        detector = MarketplaceMirrorDetector()
        results = []
        
        logger.info(f"Processing {len(marketplace_pairs)} marketplace pairs")
        
        for i, (old_url, new_url) in enumerate(marketplace_pairs):
            print(f"\nProcessing pair {i+1}/{len(marketplace_pairs)}")
            print(f"  Old: {old_url}")
            print(f"  New: {new_url}")
            
            result = detector.detect_mirror(old_url, new_url)
            results.append(result)
            
            if "classification" in result:
                print(f"  Result: {result['classification']}")
                print(f"  Confidence: {result.get('confidence_percentage', 0)}%")
        
        # Summary
        print(f"\n" + "-"*60)
        print("Batch Processing Summary:")
        print(f"Total pairs: {len(results)}")
        mirrors_found = sum(1 for r in results if "MIRROR" in r.get("classification", ""))
        print(f"Mirrors detected: {mirrors_found}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in Example 7: {e}")
        return []


def run_all_examples():
    """Run all 7 examples."""
    print("\n" + "="*60)
    print("DARKNET MARKETPLACE MIRROR DETECTION - 7 EXAMPLES")
    print("="*60)
    
    # Example 1
    example_1_single_pillar_extraction()
    
    # Example 2
    example_2_html_analysis()
    
    # Example 3
    example_3_pgp_analysis()
    
    # Example 4
    example_4_training_classifier()
    
    # Example 5
    example_5_inference_pipeline()
    
    # Example 6
    example_6_custom_weights()
    
    # Example 7
    example_7_batch_processing()
    
    print("\n" + "="*60)
    print("ALL EXAMPLES COMPLETED")
    print("="*60)


if __name__ == "__main__":
    run_all_examples()
