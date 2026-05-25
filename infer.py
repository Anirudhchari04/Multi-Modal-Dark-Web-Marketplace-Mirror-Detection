"""
Inference Script for Mirror Detection
Runs detection on real marketplace URLs
"""

import argparse
import json
import logging
import sys

from config import LOG_LEVEL, DEFAULT_MODEL_PATH
from utils import LoggingSetup
from main import MarketplaceMirrorDetector


def run_inference(old_url: str, new_url: str, model_path: str = DEFAULT_MODEL_PATH,
                  pgp_old: str = "", pgp_new: str = "", output_file: str = None) -> dict:
    """Run inference on marketplace pair."""
    logger = LoggingSetup.setup_logging("infer", LOG_LEVEL)
    
    try:
        logger.info(f"Loading model from {model_path}")
        detector = MarketplaceMirrorDetector(model_path=model_path)
        
        logger.info(f"Running detection on:")
        logger.info(f"  Old: {old_url}")
        logger.info(f"  New: {new_url}")
        
        result = detector.detect_mirror(old_url, new_url, pgp_old, pgp_new)
        
        # Save result if output file specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Results saved to {output_file}")
        
        return result
        
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }


def main():
    """CLI interface for inference."""
    parser = argparse.ArgumentParser(description="Run Mirror Detection Inference")
    parser.add_argument("old_url", help="Old marketplace URL")
    parser.add_argument("new_url", help="New marketplace URL")
    parser.add_argument("--pgp-old", help="PGP fingerprint for old marketplace", default="")
    parser.add_argument("--pgp-new", help="PGP fingerprint for new marketplace", default="")
    parser.add_argument("--model", help="Path to trained model", default=DEFAULT_MODEL_PATH)
    parser.add_argument("--output", help="Output JSON file path", default=None)
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else LOG_LEVEL
    logger = LoggingSetup.setup_logging("inference", level)
    
    # Run inference
    result = run_inference(
        args.old_url,
        args.new_url,
        args.model,
        args.pgp_old,
        args.pgp_new,
        args.output
    )
    
    # Print to stdout
    print(json.dumps(result, indent=2))
    
    # Print summary if available
    if "summary" in result:
        print(result["summary"])
    
    # Exit with appropriate code
    if result.get("status") == "failed" or "error" in result:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
