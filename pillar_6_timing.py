"""
Pillar 6: Response Timing Analysis
Analyzes response time distributions and patterns
Extracts 14 features related to timing consistency
"""

import requests
import logging
import numpy as np
from typing import List
import time
from scipy import stats

from config import HTTP_TIMEOUT, TIMING_SAMPLES
from utils import ResponseAnalyzer, DataValidator


class ResponseTimingAnalyzer:
    """Analyzes response timing patterns and distributions."""
    
    def __init__(self, timeout: int = HTTP_TIMEOUT, samples: int = TIMING_SAMPLES):
        self.timeout = timeout
        self.samples = samples
        self.logger = logging.getLogger(__name__)
    
    def collect_timing_samples(self, url: str, sample_count: int = None) -> List[float]:
        """Collect response timing samples."""
        if sample_count is None:
            sample_count = self.samples
        
        timings = []
        
        if not DataValidator.is_valid_url(url):
            self.logger.error(f"Invalid URL: {url}")
            return timings
        
        for i in range(sample_count):
            try:
                start_time = time.time()
                response = requests.get(url, timeout=self.timeout, verify=False)
                elapsed = time.time() - start_time
                timings.append(elapsed)
            except requests.Timeout:
                timings.append(self.timeout)
                self.logger.debug(f"Timeout on sample {i+1}")
            except requests.ConnectionError:
                timings.append(self.timeout)
                self.logger.debug(f"Connection error on sample {i+1}")
            except Exception as e:
                timings.append(self.timeout)
                self.logger.debug(f"Error on sample {i+1}: {e}")
        
        return timings
    
    def calculate_timing_distribution(self, timings: List[float]) -> dict:
        """Calculate timing distribution statistics."""
        if not timings:
            return {
                'mean': 0, 'std': 0, 'min': 0, 'max': 0,
                'p25': 0, 'p50': 0, 'p75': 0, 'p95': 0, 'p99': 0,
                'skewness': 0, 'kurtosis': 0
            }
        
        timings_arr = np.array(timings)
        
        try:
            skewness = float(stats.skew(timings_arr)) if len(timings_arr) > 2 else 0
            kurtosis = float(stats.kurtosis(timings_arr)) if len(timings_arr) > 2 else 0
        except Exception:
            skewness = 0
            kurtosis = 0
        
        return {
            'mean': float(np.mean(timings_arr)),
            'std': float(np.std(timings_arr)),
            'min': float(np.min(timings_arr)),
            'max': float(np.max(timings_arr)),
            'p25': float(np.percentile(timings_arr, 25)),
            'p50': float(np.percentile(timings_arr, 50)),
            'p75': float(np.percentile(timings_arr, 75)),
            'p95': float(np.percentile(timings_arr, 95)),
            'p99': float(np.percentile(timings_arr, 99)),
            'skewness': skewness,
            'kurtosis': kurtosis
        }
    
    def extract_features(self, old_url: str, new_url: str) -> np.ndarray:
        """Extract 14 response timing features."""
        features = np.zeros(14)
        
        try:
            # Collect timing samples
            old_timings = self.collect_timing_samples(old_url)
            new_timings = self.collect_timing_samples(new_url)
            
            if not old_timings or not new_timings:
                self.logger.warning("Could not collect timing samples from one or both URLs")
                return features
            
            # Calculate distributions
            old_dist = self.calculate_timing_distribution(old_timings)
            new_dist = self.calculate_timing_distribution(new_timings)
            
            # Feature 0-1: Mean response times
            features[0] = min(old_dist['mean'] / 30, 1.0)
            features[1] = min(new_dist['mean'] / 30, 1.0)
            
            # Feature 2-3: Std dev of response times
            features[2] = min(old_dist['std'] / 15, 1.0)
            features[3] = min(new_dist['std'] / 15, 1.0)
            
            # Feature 4-5: p95 response times
            features[4] = min(old_dist['p95'] / 60, 1.0)
            features[5] = min(new_dist['p95'] / 60, 1.0)
            
            # Feature 6: p95 similarity
            if max(old_dist['p95'], new_dist['p95']) > 0:
                p95_sim = min(old_dist['p95'], new_dist['p95']) / max(old_dist['p95'], new_dist['p95'])
                features[6] = p95_sim
            
            # Feature 7: Skewness consistency
            old_skew = np.clip(abs(old_dist['skewness']), 0, 10) / 10
            new_skew = np.clip(abs(new_dist['skewness']), 0, 10) / 10
            features[7] = 1.0 - abs(old_skew - new_skew)
            
            # Feature 8: Kurtosis consistency
            old_kurt = np.clip(abs(old_dist['kurtosis']), 0, 10) / 10
            new_kurt = np.clip(abs(new_dist['kurtosis']), 0, 10) / 10
            features[8] = 1.0 - abs(old_kurt - new_kurt)
            
            # Feature 9: Correlation between timing samples
            # (heuristic: if URLs are mirrors, timing patterns should correlate)
            if len(old_timings) > 1 and len(new_timings) > 1:
                min_len = min(len(old_timings), len(new_timings))
                correlation = np.corrcoef(old_timings[:min_len], new_timings[:min_len])[0, 1]
                features[9] = max(0, correlation)  # Correlation can be negative
            
            # Feature 10: Cache effectiveness (old)
            old_cache_score = self._estimate_cache_effectiveness(old_timings)
            features[10] = old_cache_score
            
            # Feature 11: Cache effectiveness (new)
            new_cache_score = self._estimate_cache_effectiveness(new_timings)
            features[11] = new_cache_score
            
            # Feature 12: Timing stability
            old_stability = self._calculate_stability(old_timings)
            new_stability = self._calculate_stability(new_timings)
            stability_sim = 1.0 - abs(old_stability - new_stability)
            features[12] = stability_sim
            
            # Feature 13: Overall fingerprint match
            features[13] = (features[6] + features[7] + features[8] + features[9]) / 4
            
            # Normalize all features to 0-1 range
            features = np.clip(features, 0, 1)
            
        except Exception as e:
            self.logger.error(f"Error extracting timing features: {e}")
        
        return features
    
    @staticmethod
    def _estimate_cache_effectiveness(timings: List[float]) -> float:
        """Estimate cache effectiveness from timing patterns."""
        try:
            if len(timings) < 5:
                return 0.5
            
            # First request vs later requests
            first_request = timings[0]
            later_requests = np.mean(timings[1:])
            
            if first_request > 0:
                improvement = (first_request - later_requests) / first_request
                return max(0, min(1, improvement))
            return 0.5
        except Exception:
            return 0.5
    
    @staticmethod
    def _calculate_stability(timings: List[float]) -> float:
        """Calculate timing stability score."""
        try:
            if len(timings) < 2:
                return 1.0
            
            # Lower variance = higher stability
            variance = np.var(timings)
            mean_time = np.mean(timings)
            
            if mean_time > 0:
                cv = variance / mean_time  # Coefficient of variation
                return 1.0 / (1.0 + cv)  # Transform to 0-1 scale
            return 0.5
        except Exception:
            return 0.5


def extract_timing_features(old_url: str, new_url: str, timeout: int = HTTP_TIMEOUT, samples: int = TIMING_SAMPLES) -> np.ndarray:
    """Convenience function to extract timing features."""
    analyzer = ResponseTimingAnalyzer(timeout=timeout, samples=samples)
    return analyzer.extract_features(old_url, new_url)
