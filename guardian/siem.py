"""
SIEM Integration Module
Export security events in formats compatible with SIEM systems
"""

import json
from datetime import datetime
from typing import Dict, Any
from .models import RiskAssessment, RiskLevel


class SIEMExporter:
    """Export security events to SIEM-compatible formats"""

    @staticmethod
    def to_cef(assessment: RiskAssessment) -> str:
        """
        Export to Common Event Format (CEF)
        Format: CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
        """
        severity = SIEMExporter._get_cef_severity(assessment.risk_level)

        # Build extension fields
        extensions = [
            f"src={assessment.login_attempt.ip_address}",
            f"suser={assessment.login_attempt.username}",
            f"outcome={'success' if assessment.login_attempt.success else 'failure'}",
            f"cs1Label=RiskScore",
            f"cs1={assessment.risk_score}",
            f"cs2Label=RiskLevel",
            f"cs2={assessment.risk_level.value}",
            f"cs3Label=Recommendation",
            f"cs3={assessment.recommendation}",
        ]

        if assessment.login_attempt.location:
            loc = assessment.login_attempt.location
            extensions.append(f"cs4Label=Location")
            extensions.append(f"cs4={loc.get('city')}, {loc.get('country')}")

        extension_str = " ".join(extensions)

        cef = (
            f"CEF:0|SmartLoginGuardian|LoginGuardian|1.0|{assessment.risk_level.value}|"
            f"Suspicious Login Detected|{severity}|{extension_str}"
        )

        return cef

    @staticmethod
    def to_leef(assessment: RiskAssessment) -> str:
        """
        Export to Log Event Extended Format (LEEF)
        Format: LEEF:Version|Vendor|Product|Version|EventID|Delimiter|Key-Value pairs
        """
        fields = {
            'src': assessment.login_attempt.ip_address,
            'usrName': assessment.login_attempt.username,
            'cat': assessment.risk_level.value,
            'sev': SIEMExporter._get_leef_severity(assessment.risk_level),
            'devTime': assessment.login_attempt.timestamp.strftime('%b %d %Y %H:%M:%S'),
            'riskScore': assessment.risk_score,
            'outcome': 'success' if assessment.login_attempt.success else 'failure',
        }

        if assessment.login_attempt.location:
            loc = assessment.login_attempt.location
            fields['srcCountry'] = loc.get('country')
            fields['srcCity'] = loc.get('city')

        field_str = '\t'.join([f"{k}={v}" for k, v in fields.items()])

        leef = f"LEEF:2.0|SmartLoginGuardian|LoginGuardian|1.0|SuspiciousLogin|\t{field_str}"

        return leef

    @staticmethod
    def to_json(assessment: RiskAssessment) -> str:
        """Export to JSON format for modern SIEM systems"""
        event = {
            'timestamp': assessment.timestamp.isoformat(),
            'event_type': 'authentication',
            'severity': assessment.risk_level.value,
            'risk_score': assessment.risk_score,
            'user': {
                'username': assessment.login_attempt.username,
            },
            'source': {
                'ip': assessment.login_attempt.ip_address,
                'user_agent': assessment.login_attempt.user_agent,
            },
            'authentication': {
                'success': assessment.login_attempt.success,
            },
            'threat': {
                'risk_level': assessment.risk_level.value,
                'risk_score': assessment.risk_score,
                'recommendation': assessment.recommendation,
                'signals': [
                    {
                        'type': signal.signal_type.value,
                        'severity': signal.severity,
                        'description': signal.description,
                        'details': signal.details
                    }
                    for signal in assessment.signals
                ]
            }
        }

        if assessment.login_attempt.location:
            event['source']['geo'] = assessment.login_attempt.location

        return json.dumps(event)

    @staticmethod
    def to_splunk(assessment: RiskAssessment) -> str:
        """Export to Splunk-friendly key-value format"""
        data = assessment.to_dict()

        auth_result = "success" if assessment.login_attempt.success else "failure"

        kv_pairs = [
            f'timestamp="{assessment.timestamp.isoformat()}"',
            f'username="{assessment.login_attempt.username}"',
            f'src_ip="{assessment.login_attempt.ip_address}"',
            f'auth_result="{auth_result}"',
            f'risk_score={assessment.risk_score}',
            f'risk_level="{assessment.risk_level.value}"',
            f'recommendation="{assessment.recommendation}"',
            f'signal_count={len(assessment.signals)}'
        ]

        if assessment.login_attempt.location:
            loc = assessment.login_attempt.location
            kv_pairs.append(f'src_country="{loc.get("country")}"')
            kv_pairs.append(f'src_city="{loc.get("city")}"')

        if assessment.signals:
            signal_types = ','.join([s.signal_type.value for s in assessment.signals])
            kv_pairs.append(f'signal_types="{signal_types}"')

        return ' '.join(kv_pairs)

    @staticmethod
    def _get_cef_severity(risk_level: RiskLevel) -> int:
        """Map risk level to CEF severity (0-10)"""
        mapping = {
            RiskLevel.SAFE: 0,
            RiskLevel.LOW: 3,
            RiskLevel.MEDIUM: 5,
            RiskLevel.HIGH: 7,
            RiskLevel.CRITICAL: 10
        }
        return mapping.get(risk_level, 5)

    @staticmethod
    def _get_leef_severity(risk_level: RiskLevel) -> int:
        """Map risk level to LEEF severity (0-10)"""
        return SIEMExporter._get_cef_severity(risk_level)
