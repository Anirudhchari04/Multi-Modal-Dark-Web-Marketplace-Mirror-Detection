"""
Main Orchestrator for Darknet Mirror Detection System
Coordinates all 7 pillars and ML pipeline
"""

import logging
import numpy as np
import argparse
from typing import Dict
import json
import sys

from config import LOG_LEVEL, LOG_FILE, HTTP_TIMEOUT, TOTAL_FEATURES
from utils import LoggingSetup
from ensemble_classifier import create_detection_pipeline, EnsembleClassifier
from pillar_1_http import extract_http_features
from pillar_2_html import extract_html_features
from pillar_3_javascript import extract_javascript_features
from pillar_4_pgp import extract_pgp_features
from pillar_5_exceptions import extract_exception_features
from pillar_6_timing import extract_timing_features
from pillar_7_api import extract_api_features


class MarketplaceMirrorDetector:
    """Main detector coordinating all pillars."""
    
    def __init__(self, model_path: str = None):
        self.logger = LoggingSetup.setup_logging("mirror_detector", LOG_LEVEL)
        self.classifier = EnsembleClassifier()
        self.pipeline = create_detection_pipeline()
        self.timeout = HTTP_TIMEOUT
        
        # Load pre-trained model if provided
        if model_path:
            self.classifier.load_model(model_path)
    
    def extract_all_features(self, old_url: str, new_url: str, pgp_old: str = "", pgp_new: str = "") -> Dict[str, np.ndarray]:
        """Extract features from all 7 pillars."""
        pillar_features = {}
        
        try:
            # Pillar 1: HTTP Response Fingerprinting
            self.logger.info("Extracting Pillar 1: HTTP Response Fingerprinting")
            pillar_features["pillar_1"] = extract_http_features(old_url, new_url, self.timeout)
        except Exception as e:
            self.logger.error(f"Error in Pillar 1: {e}")
            pillar_features["pillar_1"] = np.zeros(12)
        
        try:
            # Pillar 2: HTML/DOM Structure
            self.logger.info("Extracting Pillar 2: HTML/DOM Structure Analysis")
            pillar_features["pillar_2"] = extract_html_features(old_url, new_url, self.timeout)
        except Exception as e:
            self.logger.error(f"Error in Pillar 2: {e}")
            pillar_features["pillar_2"] = np.zeros(15)
        
        try:
            # Pillar 3: JavaScript Analysis
            self.logger.info("Extracting Pillar 3: JavaScript Code Analysis")
            pillar_features["pillar_3"] = extract_javascript_features(old_url, new_url, self.timeout)
        except Exception as e:
            self.logger.error(f"Error in Pillar 3: {e}")
            pillar_features["pillar_3"] = np.zeros(12)
        
        try:
            # Pillar 4: PGP Verification
            self.logger.info("Extracting Pillar 4: PGP Cryptographic Verification")
            if pgp_old and pgp_new:
                pillar_features["pillar_4"] = extract_pgp_features([pgp_old], [pgp_new])
            else:
                self.logger.warning("PGP fingerprints not provided, using zeros")
                pillar_features["pillar_4"] = np.zeros(12)
        except Exception as e:
            self.logger.error(f"Error in Pillar 4: {e}")
            pillar_features["pillar_4"] = np.zeros(12)
        
        try:
            # Pillar 5: Exception Handling
            self.logger.info("Extracting Pillar 5: Exception Handling Fingerprinting")
            pillar_features["pillar_5"] = extract_exception_features(old_url, new_url, self.timeout)
        except Exception as e:
            self.logger.error(f"Error in Pillar 5: {e}")
            pillar_features["pillar_5"] = np.zeros(16)
        
        try:
            # Pillar 6: Response Timing
            self.logger.info("Extracting Pillar 6: Response Timing Analysis")
            pillar_features["pillar_6"] = extract_timing_features(old_url, new_url, self.timeout)
        except Exception as e:
            self.logger.error(f"Error in Pillar 6: {e}")
            pillar_features["pillar_6"] = np.zeros(14)
        
        try:
            # Pillar 7: API Endpoints
            self.logger.info("Extracting Pillar 7: API Endpoint Analysis")
            pillar_features["pillar_7"] = extract_api_features(old_url, new_url, self.timeout)
        except Exception as e:
            self.logger.error(f"Error in Pillar 7: {e}")
            pillar_features["pillar_7"] = np.zeros(12)
        
        return pillar_features
    
    def detect_mirror(self, old_url: str, new_url: str, pgp_old: str = "", pgp_new: str = "") -> Dict:
        """Complete mirror detection pipeline."""
        try:
            self.logger.info(f"Starting mirror detection for: {old_url} vs {new_url}")
            
            # Extract features from all pillars
            pillar_features = self.extract_all_features(old_url, new_url, pgp_old, pgp_new)
            
            # Combine features
            combined_features = self.pipeline.combine_pillar_features(pillar_features)
            
            # Prepare pillar scores for reporting
            pillar_scores = {}
            for i in range(1, 8):
                pillar_key = f"pillar_{i}"
                if pillar_key in pillar_features:
                    pillar_scores[pillar_key] = np.mean(pillar_features[pillar_key])
            
            # Run detection
            result = self.pipeline.detect_mirror(combined_features, old_url, new_url, pillar_scores)
            
            self.logger.info(f"Detection complete: {result.get('classification', 'Unknown')}")
            return result
            
        except Exception as e:
            self.logger.error(f"Fatal error in detection pipeline: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "old_marketplace": old_url,
                "new_marketplace": new_url
            }


def main():
    """CLI interface for mirror detection."""
    parser = argparse.ArgumentParser(description="Darknet Marketplace Mirror Detection System")
    parser.add_argument("--old-url", help="Old marketplace URL")
    parser.add_argument("--new-url", help="New marketplace URL")
    parser.add_argument("--pgp-old", help="PGP fingerprint for old marketplace", default="")
    parser.add_argument("--pgp-new", help="PGP fingerprint for new marketplace", default="")
    parser.add_argument("--model", help="Path to trained model", default="models/mirror_detector.pkl")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    parser.add_argument("--mode", choices=["detect", "train"], default="detect", help="Operation mode")
    parser.add_argument("--training-data", help="Path to training data CSV (for training mode)")
    
    args = parser.parse_args()
    
    if args.mode == "detect":
        if not args.old_url or not args.new_url:
            parser.print_help()
            sys.exit(1)
        
        detector = MarketplaceMirrorDetector(model_path=args.model)
        result = detector.detect_mirror(args.old_url, args.new_url, args.pgp_old, args.pgp_new)
        
        # Output result
        output_json = json.dumps(result, indent=2)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output_json)
            print(f"Results saved to {args.output}")
        else:
            print(output_json)
        
        # Print summary if available
        if "summary" in result:
            print(result["summary"])
    
    elif args.mode == "train":
        if not args.training_data:
            print("Error: --training-data required for training mode")
            sys.exit(1)
        
        print("Training mode not implemented in main.py. Use train.py instead.")
        sys.exit(1)


if __name__ == "__main__":
    main()
