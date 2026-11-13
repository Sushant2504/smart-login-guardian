"""
MITRE ATT&CK Framework Integration
Maps detected threats to MITRE ATT&CK tactics, techniques, and procedures
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class MitreTactic(Enum):
    """MITRE ATT&CK Tactics"""
    INITIAL_ACCESS = "TA0001"
    EXECUTION = "TA0002"
    PERSISTENCE = "TA0003"
    PRIVILEGE_ESCALATION = "TA0004"
    DEFENSE_EVASION = "TA0005"
    CREDENTIAL_ACCESS = "TA0006"
    DISCOVERY = "TA0007"
    LATERAL_MOVEMENT = "TA0008"
    COLLECTION = "TA0009"
    COMMAND_AND_CONTROL = "TA0011"
    EXFILTRATION = "TA0010"
    IMPACT = "TA0040"


@dataclass
class MitreTechnique:
    """MITRE ATT&CK Technique"""
    technique_id: str
    name: str
    tactic: MitreTactic
    description: str
    detection: str
    mitigation: str
    sub_techniques: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'technique_id': self.technique_id,
            'name': self.name,
            'tactic': self.tactic.value,
            'tactic_name': self.tactic.name,
            'description': self.description,
            'detection': self.detection,
            'mitigation': self.mitigation,
            'sub_techniques': self.sub_techniques or []
        }


class MitreAttackMapper:
    """Maps security events to MITRE ATT&CK framework"""

    # Technique database for authentication-related attacks
    TECHNIQUES = {
        'T1110': MitreTechnique(
            technique_id='T1110',
            name='Brute Force',
            tactic=MitreTactic.CREDENTIAL_ACCESS,
            description='Adversaries may use brute force techniques to gain access to accounts when passwords are unknown or when password hashes are obtained.',
            detection='Monitor authentication logs for system and application login failures. Excessive login attempts may indicate brute force attack.',
            mitigation='Use multi-factor authentication. Implement account lockout policies. Monitor and alert on excessive failed login attempts.'
        ),
        'T1110.001': MitreTechnique(
            technique_id='T1110.001',
            name='Password Guessing',
            tactic=MitreTactic.CREDENTIAL_ACCESS,
            description='Adversaries may use a single or small list of commonly used passwords against many different accounts.',
            detection='Monitor for many failed authentication attempts across different accounts.',
            mitigation='Enforce strong password policies. Implement account lockout. Use CAPTCHA after failed attempts.'
        ),
        'T1110.003': MitreTechnique(
            technique_id='T1110.003',
            name='Password Spraying',
            tactic=MitreTactic.CREDENTIAL_ACCESS,
            description='Adversaries may use a single or small list of commonly used passwords against many accounts to avoid account lockouts.',
            detection='Monitor for authentication failures across multiple accounts from same source.',
            mitigation='Multi-factor authentication. Monitor for multiple failed logins across accounts.'
        ),
        'T1110.004': MitreTechnique(
            technique_id='T1110.004',
            name='Credential Stuffing',
            tactic=MitreTactic.CREDENTIAL_ACCESS,
            description='Adversaries may use credentials obtained from breach dumps to gain unauthorized access.',
            detection='Monitor for login attempts from unusual locations or with unusual patterns. Check against known compromised credential databases.',
            mitigation='Implement breach detection services. Force password resets for compromised credentials. Use MFA.'
        ),
        'T1078': MitreTechnique(
            technique_id='T1078',
            name='Valid Accounts',
            tactic=MitreTactic.INITIAL_ACCESS,
            description='Adversaries may obtain and abuse credentials of existing accounts.',
            detection='Monitor for account login patterns that are unusual for that account.',
            mitigation='Use MFA. Monitor login patterns. Implement risk-based authentication.'
        ),
        'T1078.004': MitreTechnique(
            technique_id='T1078.004',
            name='Cloud Accounts',
            tactic=MitreTactic.INITIAL_ACCESS,
            description='Adversaries may compromise cloud accounts to gain access to cloud services.',
            detection='Monitor cloud authentication logs for unusual access patterns, locations, or times.',
            mitigation='Enforce MFA for cloud accounts. Monitor for impossible travel. Use conditional access policies.'
        ),
        'T1534': MitreTechnique(
            technique_id='T1534',
            name='Internal Spearphishing',
            tactic=MitreTactic.LATERAL_MOVEMENT,
            description='Adversaries may use compromised accounts to send phishing messages.',
            detection='Monitor for unusual email patterns from legitimate accounts.',
            mitigation='User training. Email security controls. Monitor for account compromise.'
        ),
        'T1087': MitreTechnique(
            technique_id='T1087',
            name='Account Discovery',
            tactic=MitreTactic.DISCOVERY,
            description='Adversaries may attempt to get a listing of accounts.',
            detection='Monitor for login attempts to non-existent accounts. Track enumeration patterns.',
            mitigation='Implement consistent error messages for valid and invalid accounts. Rate limiting.'
        ),
        'T1021': MitreTechnique(
            technique_id='T1021',
            name='Remote Services',
            tactic=MitreTactic.LATERAL_MOVEMENT,
            description='Adversaries may use valid accounts to access remote systems.',
            detection='Monitor for remote login attempts, especially from unusual locations.',
            mitigation='Disable unnecessary remote services. Use network segmentation. Implement MFA.'
        ),
        'T1185': MitreTechnique(
            technique_id='T1185',
            name='Browser Session Hijacking',
            tactic=MitreTactic.COLLECTION,
            description='Adversaries may take advantage of security vulnerabilities to hijack web sessions.',
            detection='Monitor for session anomalies such as sudden IP changes or unusual session activity.',
            mitigation='Use secure session management. Implement session timeouts. Monitor for session anomalies.'
        ),
    }

    def __init__(self):
        self.techniques_by_signal = self._build_signal_mapping()

    def _build_signal_mapping(self) -> Dict[str, List[str]]:
        """Map signal types to MITRE techniques"""
        return {
            'brute_force': ['T1110', 'T1110.001'],
            'password_spray': ['T1110.003'],
            'credential_stuffing': ['T1110.004'],
            'account_enumeration': ['T1087'],
            'impossible_travel': ['T1078', 'T1078.004'],
            'unusual_location': ['T1078', 'T1078.004'],
            'unusual_time': ['T1078'],
            'session_hijacking': ['T1185'],
            'lateral_movement': ['T1021', 'T534'],
            'new_device': ['T1078'],
        }

    def map_signal_to_techniques(self, signal_type: str) -> List[MitreTechnique]:
        """Map a security signal to relevant MITRE techniques"""
        technique_ids = self.techniques_by_signal.get(signal_type, [])
        return [self.TECHNIQUES[tid] for tid in technique_ids if tid in self.TECHNIQUES]

    def get_technique(self, technique_id: str) -> Optional[MitreTechnique]:
        """Get technique details by ID"""
        return self.TECHNIQUES.get(technique_id)

    def get_all_techniques(self) -> List[MitreTechnique]:
        """Get all techniques"""
        return list(self.TECHNIQUES.values())

    def get_techniques_by_tactic(self, tactic: MitreTactic) -> List[MitreTechnique]:
        """Get all techniques for a specific tactic"""
        return [t for t in self.TECHNIQUES.values() if t.tactic == tactic]

    def enrich_assessment_with_mitre(self, assessment) -> Dict[str, Any]:
        """Enrich risk assessment with MITRE ATT&CK mappings"""
        mitre_data = {
            'tactics': set(),
            'techniques': [],
            'attack_pattern': None
        }

        for signal in assessment.signals:
            techniques = self.map_signal_to_techniques(signal.signal_type.value)
            for technique in techniques:
                mitre_data['tactics'].add(technique.tactic.name)
                mitre_data['techniques'].append(technique.to_dict())

        # Determine attack pattern
        mitre_data['attack_pattern'] = self._identify_attack_pattern(assessment.signals)
        mitre_data['tactics'] = list(mitre_data['tactics'])

        return mitre_data

    def _identify_attack_pattern(self, signals) -> Optional[str]:
        """Identify the overall attack pattern"""
        signal_types = [s.signal_type.value for s in signals]

        # Pattern detection logic
        if 'brute_force' in signal_types:
            if 'account_enumeration' in signal_types:
                return 'Targeted Brute Force Attack'
            return 'Brute Force Attack'

        if 'password_spray' in signal_types:
            return 'Password Spraying Campaign'

        if 'credential_stuffing' in signal_types:
            return 'Credential Stuffing Attack'

        if 'impossible_travel' in signal_types or 'session_hijacking' in signal_types:
            return 'Account Takeover Attempt'

        if 'lateral_movement' in signal_types:
            return 'Lateral Movement'

        if len(signal_types) >= 3:
            return 'Multi-Vector Attack'

        return 'Suspicious Activity'
