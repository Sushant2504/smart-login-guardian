"""
Advanced Threat Intelligence Engine
Integrates with multiple threat feeds and provides IP reputation, IOC matching, and enrichment
"""

import requests
import hashlib
import ipaddress
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json


class ThreatLevel(Enum):
    """Threat severity levels"""
    CLEAN = "clean"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ThreatIntelligence:
    """Threat intelligence data for an indicator"""
    indicator: str
    indicator_type: str  # ip, domain, hash, email
    threat_level: ThreatLevel
    confidence: int  # 0-100
    sources: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    threat_types: List[str] = field(default_factory=list)
    geo_location: Optional[Dict[str, Any]] = None
    asn: Optional[str] = None
    is_proxy: bool = False
    is_tor: bool = False
    is_vpn: bool = False
    abuse_score: int = 0
    malware_families: List[str] = field(default_factory=list)
    attack_types: List[str] = field(default_factory=list)
    related_indicators: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'indicator': self.indicator,
            'indicator_type': self.indicator_type,
            'threat_level': self.threat_level.value,
            'confidence': self.confidence,
            'sources': self.sources,
            'tags': self.tags,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'threat_types': self.threat_types,
            'geo_location': self.geo_location,
            'asn': self.asn,
            'is_proxy': self.is_proxy,
            'is_tor': self.is_tor,
            'is_vpn': self.is_vpn,
            'abuse_score': self.abuse_score,
            'malware_families': self.malware_families,
            'attack_types': self.attack_types,
            'related_indicators': self.related_indicators
        }


class ThreatIntelEngine:
    """
    Enterprise Threat Intelligence Engine
    Aggregates data from multiple sources and provides unified threat intelligence
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = self.config.get('cache_ttl', 3600)  # 1 hour default

        # API keys from config
        self.abuseipdb_key = self.config.get('abuseipdb_api_key')
        self.virustotal_key = self.config.get('virustotal_api_key')
        self.alienvault_key = self.config.get('alienvault_api_key')

        # Known malicious IPs/patterns (can be loaded from feeds)
        self.known_bad_ips = set()
        self.known_tor_exits = set()
        self.known_vpn_providers = set()

    def enrich_ip(self, ip_address: str) -> ThreatIntelligence:
        """
        Enrich IP address with threat intelligence from multiple sources
        """
        # Check cache
        cache_key = f"ip:{ip_address}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return cached_data

        # Initialize threat intel object
        intel = ThreatIntelligence(
            indicator=ip_address,
            indicator_type='ip',
            threat_level=ThreatLevel.CLEAN,
            confidence=0
        )

        # Check if private IP
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            if ip_obj.is_private:
                intel.tags.append('private_ip')
                intel.confidence = 100
                self._cache_result(cache_key, intel)
                return intel
        except ValueError:
            intel.threat_level = ThreatLevel.HIGH
            intel.tags.append('invalid_ip')
            intel.confidence = 100
            return intel

        # Aggregate intelligence from multiple sources
        sources_data = []

        # AbuseIPDB
        if self.abuseipdb_key:
            abuseipdb_data = self._check_abuseipdb(ip_address)
            if abuseipdb_data:
                sources_data.append(abuseipdb_data)

        # VirusTotal
        if self.virustotal_key:
            vt_data = self._check_virustotal(ip_address)
            if vt_data:
                sources_data.append(vt_data)

        # AlienVault OTX
        if self.alienvault_key:
            otx_data = self._check_alienvault_otx(ip_address)
            if otx_data:
                sources_data.append(otx_data)

        # Local blacklists
        local_data = self._check_local_blacklists(ip_address)
        if local_data:
            sources_data.append(local_data)

        # Aggregate results
        intel = self._aggregate_intelligence(ip_address, sources_data)

        # Cache result
        self._cache_result(cache_key, intel)

        return intel

    def _check_abuseipdb(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Check AbuseIPDB for IP reputation"""
        if not self.abuseipdb_key:
            return None

        try:
            url = 'https://api.abuseipdb.com/api/v2/check'
            headers = {
                'Accept': 'application/json',
                'Key': self.abuseipdb_key
            }
            params = {
                'ipAddress': ip_address,
                'maxAgeInDays': 90,
                'verbose': True
            }

            response = requests.get(url, headers=headers, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json().get('data', {})
                return {
                    'source': 'AbuseIPDB',
                    'abuse_score': data.get('abuseConfidenceScore', 0),
                    'total_reports': data.get('totalReports', 0),
                    'threat_types': data.get('usageType', '').split(','),
                    'is_tor': data.get('isTor', False),
                    'country': data.get('countryCode'),
                    'isp': data.get('isp')
                }
        except Exception as e:
            print(f"AbuseIPDB check failed: {e}")

        return None

    def _check_virustotal(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Check VirusTotal for IP reputation"""
        if not self.virustotal_key:
            return None

        try:
            url = f'https://www.virustotal.com/api/v3/ip_addresses/{ip_address}'
            headers = {
                'x-apikey': self.virustotal_key
            }

            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 200:
                data = response.json().get('data', {}).get('attributes', {})
                stats = data.get('last_analysis_stats', {})

                return {
                    'source': 'VirusTotal',
                    'malicious_votes': stats.get('malicious', 0),
                    'suspicious_votes': stats.get('suspicious', 0),
                    'harmless_votes': stats.get('harmless', 0),
                    'country': data.get('country'),
                    'asn': str(data.get('asn', '')),
                    'reputation': data.get('reputation', 0)
                }
        except Exception as e:
            print(f"VirusTotal check failed: {e}")

        return None

    def _check_alienvault_otx(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Check AlienVault OTX for IP intelligence"""
        if not self.alienvault_key:
            return None

        try:
            url = f'https://otx.alienvault.com/api/v1/indicators/IPv4/{ip_address}/general'
            headers = {
                'X-OTX-API-KEY': self.alienvault_key
            }

            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 200:
                data = response.json()

                return {
                    'source': 'AlienVault OTX',
                    'pulse_count': data.get('pulse_info', {}).get('count', 0),
                    'tags': data.get('pulse_info', {}).get('tags', []),
                    'malware_families': data.get('malware_families', []),
                    'reputation': data.get('reputation', 0)
                }
        except Exception as e:
            print(f"AlienVault OTX check failed: {e}")

        return None

    def _check_local_blacklists(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Check local blacklists and threat feeds"""
        result = {
            'source': 'Local Intelligence',
            'is_blacklisted': ip_address in self.known_bad_ips,
            'is_tor': ip_address in self.known_tor_exits,
            'is_vpn': ip_address in self.known_vpn_providers
        }

        if any([result['is_blacklisted'], result['is_tor'], result['is_vpn']]):
            return result

        return None

    def _aggregate_intelligence(self, ip_address: str, sources_data: List[Dict[str, Any]]) -> ThreatIntelligence:
        """Aggregate intelligence from multiple sources"""
        intel = ThreatIntelligence(
            indicator=ip_address,
            indicator_type='ip',
            threat_level=ThreatLevel.CLEAN,
            confidence=0
        )

        if not sources_data:
            return intel

        # Extract data from sources
        total_abuse_score = 0
        abuse_count = 0
        malicious_votes = 0
        total_sources = len(sources_data)

        for source_data in sources_data:
            intel.sources.append(source_data.get('source', 'Unknown'))

            # Abuse score
            if 'abuse_score' in source_data:
                total_abuse_score += source_data['abuse_score']
                abuse_count += 1

            # Malicious votes
            if 'malicious_votes' in source_data:
                malicious_votes += source_data['malicious_votes']

            # Tags
            if 'tags' in source_data:
                intel.tags.extend(source_data['tags'])

            # Threat types
            if 'threat_types' in source_data:
                intel.threat_types.extend(source_data['threat_types'])

            # Malware families
            if 'malware_families' in source_data:
                intel.malware_families.extend(source_data['malware_families'])

            # Flags
            if source_data.get('is_tor'):
                intel.is_tor = True
                intel.tags.append('tor_exit')

            if source_data.get('is_vpn'):
                intel.is_vpn = True
                intel.tags.append('vpn')

            if source_data.get('is_blacklisted'):
                intel.tags.append('blacklisted')

            # Geographic data
            if 'country' in source_data and not intel.geo_location:
                intel.geo_location = {'country': source_data['country']}

            if 'asn' in source_data and not intel.asn:
                intel.asn = source_data['asn']

        # Calculate final abuse score
        if abuse_count > 0:
            intel.abuse_score = int(total_abuse_score / abuse_count)

        # Determine threat level based on aggregated data
        if intel.abuse_score >= 80 or malicious_votes >= 5 or 'blacklisted' in intel.tags:
            intel.threat_level = ThreatLevel.CRITICAL
            intel.confidence = 95
        elif intel.abuse_score >= 50 or malicious_votes >= 3:
            intel.threat_level = ThreatLevel.HIGH
            intel.confidence = 85
        elif intel.abuse_score >= 25 or malicious_votes >= 1:
            intel.threat_level = ThreatLevel.MEDIUM
            intel.confidence = 70
        elif intel.abuse_score >= 10 or intel.is_tor or intel.is_vpn:
            intel.threat_level = ThreatLevel.LOW
            intel.confidence = 60
        else:
            intel.threat_level = ThreatLevel.CLEAN
            intel.confidence = 50

        # Deduplicate tags
        intel.tags = list(set(intel.tags))
        intel.threat_types = list(set(intel.threat_types))

        return intel

    def _cache_result(self, key: str, data: ThreatIntelligence):
        """Cache threat intelligence result"""
        self.cache[key] = (data, datetime.now())

    def add_to_blacklist(self, ip_address: str):
        """Add IP to local blacklist"""
        self.known_bad_ips.add(ip_address)

    def remove_from_blacklist(self, ip_address: str):
        """Remove IP from local blacklist"""
        self.known_bad_ips.discard(ip_address)

    def load_threat_feed(self, feed_url: str, feed_type: str = 'ip'):
        """Load threat feed from URL"""
        try:
            response = requests.get(feed_url, timeout=10)
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if feed_type == 'ip':
                            self.known_bad_ips.add(line)
                        elif feed_type == 'tor':
                            self.known_tor_exits.add(line)
                        elif feed_type == 'vpn':
                            self.known_vpn_providers.add(line)
                return len(lines)
        except Exception as e:
            print(f"Failed to load threat feed: {e}")
        return 0

    def get_statistics(self) -> Dict[str, Any]:
        """Get threat intelligence statistics"""
        return {
            'blacklisted_ips': len(self.known_bad_ips),
            'tor_exits': len(self.known_tor_exits),
            'vpn_providers': len(self.known_vpn_providers),
            'cache_size': len(self.cache)
        }
