"""
AeroGhost IP Geolocation Module.
Uses the free ip-api.com JSON endpoint (no API key required, 45 req/min).
"""

import requests
import logging
import random
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# In-memory cache to avoid redundant lookups
_geo_cache: Dict[str, Dict] = {}

# Demo locations for localhost/private IPs
_DEMO_LOCATIONS = [
    {"city": "Moscow", "country": "Russia", "countryCode": "RU", "lat": 55.7558, "lon": 37.6173, "isp": "Rostelecom", "org": "Unknown"},
    {"city": "Beijing", "country": "China", "countryCode": "CN", "lat": 39.9042, "lon": 116.4074, "isp": "China Telecom", "org": "Unknown"},
    {"city": "Pyongyang", "country": "North Korea", "countryCode": "KP", "lat": 39.0392, "lon": 125.7625, "isp": "Star JV", "org": "Unknown"},
    {"city": "Tehran", "country": "Iran", "countryCode": "IR", "lat": 35.6892, "lon": 51.3890, "isp": "TIC", "org": "Unknown"},
    {"city": "Lagos", "country": "Nigeria", "countryCode": "NG", "lat": 6.5244, "lon": 3.3792, "isp": "MTN Nigeria", "org": "Unknown"},
    {"city": "Bucharest", "country": "Romania", "countryCode": "RO", "lat": 44.4268, "lon": 26.1025, "isp": "RCS & RDS", "org": "Unknown"},
    {"city": "Sao Paulo", "country": "Brazil", "countryCode": "BR", "lat": -23.5505, "lon": -46.6333, "isp": "Vivo", "org": "Unknown"},
]


def _is_private_ip(ip: str) -> bool:
    """Check if an IP is private/local."""
    return (
        ip.startswith("127.") or
        ip.startswith("10.") or
        ip.startswith("192.168.") or
        ip.startswith("172.16.") or
        ip == "localhost" or
        ip == "::1"
    )


def lookup_ip(ip: str) -> Optional[Dict]:
    """
    Look up geolocation for an IP address.
    Returns dict with: city, country, countryCode, lat, lon, isp, org
    Returns None on failure.
    """
    # Check cache first
    if ip in _geo_cache:
        return _geo_cache[ip]

    # For private/local IPs, return a randomized demo location
    if _is_private_ip(ip):
        demo = random.choice(_DEMO_LOCATIONS).copy()
        demo["query"] = ip
        demo["note"] = "Demo location (local IP)"
        _geo_cache[ip] = demo
        return demo

    # Query the free ip-api.com endpoint
    try:
        resp = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,message,country,countryCode,city,lat,lon,isp,org,query"},
            timeout=5
        )
        data = resp.json()

        if data.get("status") == "success":
            result = {
                "city": data.get("city", "Unknown"),
                "country": data.get("country", "Unknown"),
                "countryCode": data.get("countryCode", "??"),
                "lat": data.get("lat", 0),
                "lon": data.get("lon", 0),
                "isp": data.get("isp", "Unknown"),
                "org": data.get("org", "Unknown"),
                "query": ip,
            }
            _geo_cache[ip] = result
            return result
        else:
            logger.warning(f"Geo lookup failed for {ip}: {data.get('message')}")
            return None

    except Exception as e:
        logger.warning(f"Geo lookup error for {ip}: {e}")
        return None
