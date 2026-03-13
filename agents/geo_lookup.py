"""
AeroGhost IP Geolocation Module.
Uses the free ip-api.com JSON endpoint (no API key required, 45 req/min).
"""

import requests
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# In-memory cache to avoid redundant lookups
_geo_cache: Dict[str, Dict] = {}

# Cached server public IP geo (resolved once)
_server_geo: Optional[Dict] = None


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


def _get_server_public_geo() -> Optional[Dict]:
    """
    Resolve the server's own public IP geolocation.
    Calls ip-api.com with no IP argument, which returns the caller's public IP info.
    Result is cached so this only makes one external request.
    """
    global _server_geo
    if _server_geo is not None:
        return _server_geo

    try:
        resp = requests.get(
            "http://ip-api.com/json/",
            params={"fields": "status,message,country,countryCode,city,lat,lon,isp,org,query"},
            timeout=5,
        )
        data = resp.json()
        if data.get("status") == "success":
            _server_geo = {
                "city": data.get("city", "Unknown"),
                "country": data.get("country", "Unknown"),
                "countryCode": data.get("countryCode", "??"),
                "lat": data.get("lat", 0),
                "lon": data.get("lon", 0),
                "isp": data.get("isp", "Unknown"),
                "org": data.get("org", "Unknown"),
                "query": data.get("query", "Unknown"),
            }
            logger.info(f"Resolved server public IP: {_server_geo['query']} ({_server_geo['city']}, {_server_geo['country']})")
            return _server_geo
        else:
            logger.warning(f"Server public IP lookup failed: {data.get('message')}")
    except Exception as e:
        logger.warning(f"Server public IP lookup error: {e}")

    return None


def lookup_ip(ip: str) -> Optional[Dict]:
    """
    Look up geolocation for an IP address.
    Returns dict with: city, country, countryCode, lat, lon, isp, org
    Returns None on failure.
    """
    # Check cache first
    if ip in _geo_cache:
        return _geo_cache[ip]

    # For private/local IPs, resolve using the server's public IP
    if _is_private_ip(ip):
        server_geo = _get_server_public_geo()
        if server_geo:
            result = server_geo.copy()
            result["query"] = server_geo["query"]  # Show the real public IP
            result["original_ip"] = ip  # Keep the original private IP for reference
            result["note"] = f"Resolved via server public IP (original: {ip})"
            _geo_cache[ip] = result
            return result
        else:
            logger.warning(f"Could not resolve geolocation for private IP {ip} — server public IP lookup failed")
            return None

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
