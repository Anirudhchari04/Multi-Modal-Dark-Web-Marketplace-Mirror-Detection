"""
Test Data Generator
Generates synthetic training data and sample files for testing
"""

import numpy as np
import pandas as pd
import csv
import os
import logging

from config import TOTAL_FEATURES, LOG_LEVEL
from utils import LoggingSetup


def generate_training_data_csv(output_path: str = "training_data.csv", num_samples: int = 500) -> bool:
    """Generate synthetic training data CSV."""
    logger = LoggingSetup.setup_logging("data_gen", LOG_LEVEL)
    
    try:
        np.random.seed(42)
        
        # Generate features
        X = []
        y = []
        
        # Mirrors (positive class)
        mirrors = np.random.uniform(0.6, 1.0, (num_samples // 2, TOTAL_FEATURES))
        X.extend(mirrors)
        y.extend([1] * (num_samples // 2))
        
        # Non-mirrors (negative class)
        non_mirrors = np.random.uniform(0.0, 0.4, (num_samples // 2, TOTAL_FEATURES))
        X.extend(non_mirrors)
        y.extend([0] * (num_samples // 2))
        
        # Create DataFrame
        data = np.array(X)
        columns = [f"feature_{i}" for i in range(TOTAL_FEATURES)]
        df = pd.DataFrame(data, columns=columns)
        df['label'] = y
        
        # Shuffle
        df = df.sample(frac=1).reset_index(drop=True)
        
        # Save
        df.to_csv(output_path, index=False)
        logger.info(f"Generated training data: {output_path} ({len(df)} rows)")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating training data: {e}")
        return False


def generate_pgp_sample_files() -> dict:
    """Generate sample PGP key files."""
    logger = LoggingSetup.setup_logging("pgp_gen", LOG_LEVEL)
    
    try:
        files = {}
        
        # Sample marketplace 1
        pgp1_content = """-----BEGIN PGP PUBLIC KEY BLOCK-----
mI0EXXX1AAEDAODxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxQEAyQEA
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
=ABC1
-----END PGP PUBLIC KEY BLOCK-----"""
        
        files['marketplace1.pgp'] = pgp1_content
        
        # Sample marketplace 2
        pgp2_content = """-----BEGIN PGP PUBLIC KEY BLOCK-----
mI0EXXX2AAEDAODxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxQEAyQEA
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
=ABC2
-----END PGP PUBLIC KEY BLOCK-----"""
        
        files['marketplace2.pgp'] = pgp2_content
        
        logger.info(f"Generated {len(files)} sample PGP files")
        return files
        
    except Exception as e:
        logger.error(f"Error generating PGP files: {e}")
        return {}


def generate_test_urls() -> list:
    """Generate sample marketplace URL pairs."""
    sample_pairs = [
        {
            "old_marketplace": "http://darknet-market1.onion",
            "new_marketplace": "http://darknet-market1-mirror.onion",
            "likely_mirror": True
        },
        {
            "old_marketplace": "http://darknet-market2.onion",
            "new_marketplace": "http://different-site.onion",
            "likely_mirror": False
        },
        {
            "old_marketplace": "http://tradingpost.onion",
            "new_marketplace": "http://tradingpost-backup.onion",
            "likely_mirror": True
        }
    ]
    
    return sample_pairs


def generate_feature_ranges_reference() -> dict:
    """Generate reference for expected feature ranges."""
    ranges = {
        "pillar_1_http": {
            "response_time_mean": (0, 60),
            "response_time_std": (0, 30),
            "response_time_p95": (0, 120),
            "response_time_p99": (0, 150),
            "status_code_mode": (100, 600),
            "status_code_variance": (0, 100),
            "server_header_consistency": (0, 1),
            "x_powered_by_presence": (0, 1),
            "x_powered_by_consistency": (0, 1),
            "error_rate": (0, 1),
            "timeout_rate": (0, 1),
            "variance_coefficient": (0, 1)
        },
        "pillar_2_html": {
            "dom_depth": (0, 50),
            "tag_count": (0, 1000),
            "tag_frequency_jaccard": (0, 1),
            "css_classes_jaccard": (0, 1),
            "form_similarity": (0, 1),
            "input_similarity": (0, 1),
            "header_consistency": (0, 1),
            "link_density": (0, 1),
            "image_density": (0, 1),
            "script_similarity": (0, 1),
            "meta_consistency": (0, 1)
        },
        "pillar_3_javascript": {
            "function_overlap": (0, 1),
            "variable_overlap": (0, 1),
            "total_overlap": (0, 1),
            "function_count": (0, 100),
            "variable_count": (0, 500),
            "size_similarity": (0, 1),
            "file_count_similarity": (0, 1),
            "naming_consistency": (0, 1),
            "complexity": (0, 1),
            "minification": (0, 1)
        },
        "pillar_4_pgp": {
            "exact_match": (0, 1),
            "partial_overlap": (0, 1),
            "jaccard_similarity": (0, 1),
            "key_count": (0, 20),
            "length_consistency": (0, 1),
            "age_consistency": (0, 1),
            "freshness": (0, 1),
            "strength": (0, 1),
            "uniqueness": (0, 1)
        }
    }
    
    return ranges


def main():
    """Generate all test data."""
    logger = LoggingSetup.setup_logging("main", LOG_LEVEL)
    
    logger.info("Generating test data...")
    
    # Generate CSV
    generate_training_data_csv("training_data.csv", num_samples=500)
    
    # Generate PGP files
    pgp_files = generate_pgp_sample_files()
    for filename, content in pgp_files.items():
        with open(filename, 'w') as f:
            f.write(content)
        logger.info(f"Created {filename}")
    
    # Generate test URLs
    test_urls = generate_test_urls()
    with open("test_urls.json", 'w') as f:
        import json
        json.dump(test_urls, f, indent=2)
    logger.info("Created test_urls.json")
    
    # Generate reference
    ranges = generate_feature_ranges_reference()
    with open("feature_ranges_reference.json", 'w') as f:
        import json
        json.dump(ranges, f, indent=2)
    logger.info("Created feature_ranges_reference.json")
    
    logger.info("Test data generation complete")


if __name__ == "__main__":
    main()
