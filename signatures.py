from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
import json
import time

@dataclass
class HTTPSignature:
    response_time_mean: float = 0.0
    response_time_std: float = 0.0
    response_time_p95: float = 0.0
    response_time_p99: float = 0.0
    status_code_mode: int = 0
    status_code_variance: float = 0.0
    server_header: Optional[str] = None
    x_powered_by: Optional[str] = None
    consistent_server_header: bool = False
    consistent_x_powered_by: bool = False
    error_rate: float = 0.0
    timeout_rate: float = 0.0

@dataclass
class PGPSignature:
    fingerprints: List[str] = field(default_factory=list)
    subkeys: List[str] = field(default_factory=list)
    algorithms: List[str] = field(default_factory=list)
    key_sizes: List[int] = field(default_factory=list)
    creation_dates: List[float] = field(default_factory=list) # timestamps
    uids: List[str] = field(default_factory=list)
    raw_keys: List[str] = field(default_factory=list) # Store raw text for potential re-parsing

@dataclass
class HTMLSignature:
    dom_depth: int = 0
    tag_counts: Dict[str, int] = field(default_factory=dict)
    css_classes: List[str] = field(default_factory=list)
    form_info: Dict[str, int] = field(default_factory=dict)
    link_density: float = 0.0
    image_density: float = 0.0
    meta_tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class SiteSignature:
    """Complete digital fingerprint of a darknet site."""
    url: str
    timestamp: float = field(default_factory=time.time)
    label: Optional[str] = None # e.g., "AlphaBay", "Dread"
    http: HTTPSignature = field(default_factory=HTTPSignature)
    pgp: PGPSignature = field(default_factory=PGPSignature)
    html: HTMLSignature = field(default_factory=HTMLSignature)
    # Add other pillars here as we refactor them
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SiteSignature':
        # Reconstruct complex nested objects
        http_data = data.get('http', {})
        pgp_data = data.get('pgp', {})
        html_data = data.get('html', {})
        
        return cls(
            url=data['url'],
            timestamp=data.get('timestamp', time.time()),
            label=data.get('label'),
            http=HTTPSignature(**http_data),
            pgp=PGPSignature(**pgp_data),
            html=HTMLSignature(**html_data)
        )
