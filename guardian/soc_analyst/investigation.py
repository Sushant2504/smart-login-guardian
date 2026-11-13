"""
SOC Analyst Investigation Workspace
Provides tools for security analysts to investigate incidents, pivot through data, and build cases
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid


class CaseStatus(Enum):
    """Investigation case status"""
    NEW = "new"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    CLOSED = "closed"


class CaseSeverity(Enum):
    """Case severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceType(Enum):
    """Types of evidence"""
    LOGIN_ATTEMPT = "login_attempt"
    IP_ADDRESS = "ip_address"
    USER_ACCOUNT = "user_account"
    THREAT_INTEL = "threat_intel"
    NETWORK_TRAFFIC = "network_traffic"
    MALWARE_SAMPLE = "malware_sample"
    LOG_ENTRY = "log_entry"
    SCREENSHOT = "screenshot"
    NOTE = "note"


@dataclass
class Evidence:
    """Evidence item in an investigation"""
    evidence_id: str
    evidence_type: EvidenceType
    description: str
    data: Dict[str, Any]
    collected_at: datetime
    collected_by: str
    tags: List[str] = field(default_factory=list)
    chain_of_custody: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'evidence_id': self.evidence_id,
            'evidence_type': self.evidence_type.value,
            'description': self.description,
            'data': self.data,
            'collected_at': self.collected_at.isoformat(),
            'collected_by': self.collected_by,
            'tags': self.tags,
            'chain_of_custody': self.chain_of_custody
        }


@dataclass
class InvestigationNote:
    """Analyst note in an investigation"""
    note_id: str
    analyst: str
    timestamp: datetime
    content: str
    note_type: str = "general"  # general, hypothesis, finding, action
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'note_id': self.note_id,
            'analyst': self.analyst,
            'timestamp': self.timestamp.isoformat(),
            'content': self.content,
            'note_type': self.note_type,
            'tags': self.tags
        }


@dataclass
class TimelineEvent:
    """Event in investigation timeline"""
    event_id: str
    timestamp: datetime
    event_type: str
    description: str
    source: str
    data: Dict[str, Any]
    related_entities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type,
            'description': self.description,
            'source': self.source,
            'data': self.data,
            'related_entities': self.related_entities
        }


@dataclass
class InvestigationCase:
    """Security investigation case"""
    case_id: str
    title: str
    description: str
    severity: CaseSeverity
    status: CaseStatus
    created_at: datetime
    created_by: str
    assigned_to: Optional[str] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    notes: List[InvestigationNote] = field(default_factory=list)
    timeline: List[TimelineEvent] = field(default_factory=list)
    related_cases: List[str] = field(default_factory=list)
    indicators: Dict[str, List[str]] = field(default_factory=dict)  # type -> [values]
    mitre_techniques: List[str] = field(default_factory=list)
    resolution: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'case_id': self.case_id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'assigned_to': self.assigned_to,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'tags': self.tags,
            'evidence_count': len(self.evidence),
            'notes_count': len(self.notes),
            'timeline_events': len(self.timeline),
            'related_cases': self.related_cases,
            'indicators': self.indicators,
            'mitre_techniques': self.mitre_techniques,
            'resolution': self.resolution,
            'metrics': self.metrics
        }


class InvestigationWorkspace:
    """
    SOC Analyst Investigation Workspace
    Provides tools for managing investigations, collecting evidence, and analyzing threats
    """

    def __init__(self):
        self.cases: Dict[str, InvestigationCase] = {}
        self.pivot_cache: Dict[str, List[Any]] = {}

    def create_case(
        self,
        title: str,
        description: str,
        severity: CaseSeverity,
        created_by: str,
        tags: Optional[List[str]] = None
    ) -> InvestigationCase:
        """Create a new investigation case"""
        case = InvestigationCase(
            case_id=str(uuid.uuid4()),
            title=title,
            description=description,
            severity=severity,
            status=CaseStatus.NEW,
            created_at=datetime.utcnow(),
            created_by=created_by,
            tags=tags or []
        )

        self.cases[case.case_id] = case
        return case

    def add_evidence(
        self,
        case_id: str,
        evidence_type: EvidenceType,
        description: str,
        data: Dict[str, Any],
        collected_by: str,
        tags: Optional[List[str]] = None
    ) -> Evidence:
        """Add evidence to a case"""
        case = self.cases.get(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")

        evidence = Evidence(
            evidence_id=str(uuid.uuid4()),
            evidence_type=evidence_type,
            description=description,
            data=data,
            collected_at=datetime.utcnow(),
            collected_by=collected_by,
            tags=tags or []
        )

        evidence.chain_of_custody.append({
            'action': 'collected',
            'timestamp': datetime.utcnow().isoformat(),
            'analyst': collected_by
        })

        case.evidence.append(evidence)
        case.updated_at = datetime.utcnow()

        return evidence

    def add_note(
        self,
        case_id: str,
        analyst: str,
        content: str,
        note_type: str = "general",
        tags: Optional[List[str]] = None
    ) -> InvestigationNote:
        """Add analyst note to a case"""
        case = self.cases.get(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")

        note = InvestigationNote(
            note_id=str(uuid.uuid4()),
            analyst=analyst,
            timestamp=datetime.utcnow(),
            content=content,
            note_type=note_type,
            tags=tags or []
        )

        case.notes.append(note)
        case.updated_at = datetime.utcnow()

        return note

    def add_timeline_event(
        self,
        case_id: str,
        timestamp: datetime,
        event_type: str,
        description: str,
        source: str,
        data: Dict[str, Any],
        related_entities: Optional[List[str]] = None
    ) -> TimelineEvent:
        """Add event to case timeline"""
        case = self.cases.get(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")

        event = TimelineEvent(
            event_id=str(uuid.uuid4()),
            timestamp=timestamp,
            event_type=event_type,
            description=description,
            source=source,
            data=data,
            related_entities=related_entities or []
        )

        case.timeline.append(event)
        case.timeline.sort(key=lambda x: x.timestamp)
        case.updated_at = datetime.utcnow()

        return event

    def update_case_status(self, case_id: str, status: CaseStatus, analyst: str):
        """Update case status"""
        case = self.cases.get(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")

        old_status = case.status
        case.status = status
        case.updated_at = datetime.utcnow()

        if status in [CaseStatus.RESOLVED, CaseStatus.FALSE_POSITIVE, CaseStatus.CLOSED]:
            case.closed_at = datetime.utcnow()

        # Add note about status change
        self.add_note(
            case_id,
            analyst,
            f"Status changed from {old_status.value} to {status.value}",
            note_type="action"
        )

    def assign_case(self, case_id: str, analyst: str, assigned_by: str):
        """Assign case to analyst"""
        case = self.cases.get(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")

        old_assignee = case.assigned_to
        case.assigned_to = analyst
        case.updated_at = datetime.utcnow()

        self.add_note(
            case_id,
            assigned_by,
            f"Case assigned from {old_assignee or 'unassigned'} to {analyst}",
            note_type="action"
        )

    def add_indicator(self, case_id: str, indicator_type: str, indicator_value: str):
        """Add indicator of compromise to case"""
        case = self.cases.get(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")

        if indicator_type not in case.indicators:
            case.indicators[indicator_type] = []

        if indicator_value not in case.indicators[indicator_type]:
            case.indicators[indicator_type].append(indicator_value)
            case.updated_at = datetime.utcnow()

    def link_mitre_technique(self, case_id: str, technique_id: str):
        """Link MITRE ATT&CK technique to case"""
        case = self.cases.get(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")

        if technique_id not in case.mitre_techniques:
            case.mitre_techniques.append(technique_id)
            case.updated_at = datetime.utcnow()

    def link_related_cases(self, case_id: str, related_case_id: str):
        """Link related cases"""
        case = self.cases.get(case_id)
        related_case = self.cases.get(related_case_id)

        if not case or not related_case:
            raise ValueError("One or both cases not found")

        if related_case_id not in case.related_cases:
            case.related_cases.append(related_case_id)

        if case_id not in related_case.related_cases:
            related_case.related_cases.append(case_id)

    def pivot_by_ip(self, ip_address: str, storage) -> Dict[str, Any]:
        """
        Pivot through data by IP address
        Find all related login attempts, users, and patterns
        """
        results = {
            'ip_address': ip_address,
            'login_attempts': [],
            'affected_users': set(),
            'time_range': None,
            'countries': set(),
            'success_count': 0,
            'failure_count': 0
        }

        # Get all login attempts for this IP
        for attempt in storage.login_history:
            if attempt.ip_address == ip_address:
                results['login_attempts'].append(attempt)
                results['affected_users'].add(attempt.username)

                if attempt.success:
                    results['success_count'] += 1
                else:
                    results['failure_count'] += 1

                if attempt.location:
                    results['countries'].add(attempt.location.get('country', 'Unknown'))

        if results['login_attempts']:
            timestamps = [a.timestamp for a in results['login_attempts']]
            results['time_range'] = {
                'start': min(timestamps).isoformat(),
                'end': max(timestamps).isoformat()
            }

        results['affected_users'] = list(results['affected_users'])
        results['countries'] = list(results['countries'])

        return results

    def pivot_by_user(self, username: str, storage) -> Dict[str, Any]:
        """
        Pivot through data by username
        Find all related IPs, locations, and devices
        """
        results = {
            'username': username,
            'login_attempts': [],
            'source_ips': set(),
            'countries': set(),
            'devices': set(),
            'success_count': 0,
            'failure_count': 0,
            'anomalies': []
        }

        # Get all login attempts for this user
        for attempt in storage.login_history:
            if attempt.username == username:
                results['login_attempts'].append(attempt)
                results['source_ips'].add(attempt.ip_address)

                if attempt.success:
                    results['success_count'] += 1
                else:
                    results['failure_count'] += 1

                if attempt.location:
                    results['countries'].add(attempt.location.get('country', 'Unknown'))

                if attempt.device_fingerprint:
                    results['devices'].add(attempt.device_fingerprint)

        results['source_ips'] = list(results['source_ips'])
        results['countries'] = list(results['countries'])
        results['devices'] = list(results['devices'])

        return results

    def get_case(self, case_id: str) -> Optional[InvestigationCase]:
        """Get case by ID"""
        return self.cases.get(case_id)

    def get_cases_by_status(self, status: CaseStatus) -> List[InvestigationCase]:
        """Get all cases with specific status"""
        return [case for case in self.cases.values() if case.status == status]

    def get_cases_by_analyst(self, analyst: str) -> List[InvestigationCase]:
        """Get all cases assigned to analyst"""
        return [case for case in self.cases.values() if case.assigned_to == analyst]

    def search_cases(
        self,
        query: Optional[str] = None,
        severity: Optional[CaseSeverity] = None,
        status: Optional[CaseStatus] = None,
        tags: Optional[List[str]] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None
    ) -> List[InvestigationCase]:
        """Search cases with filters"""
        results = list(self.cases.values())

        if query:
            query_lower = query.lower()
            results = [
                case for case in results
                if query_lower in case.title.lower() or query_lower in case.description.lower()
            ]

        if severity:
            results = [case for case in results if case.severity == severity]

        if status:
            results = [case for case in results if case.status == status]

        if tags:
            results = [
                case for case in results
                if any(tag in case.tags for tag in tags)
            ]

        if created_after:
            results = [case for case in results if case.created_at >= created_after]

        if created_before:
            results = [case for case in results if case.created_at <= created_before]

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get investigation workspace statistics"""
        total_cases = len(self.cases)

        status_counts = {}
        for status in CaseStatus:
            status_counts[status.value] = len(self.get_cases_by_status(status))

        severity_counts = {}
        for severity in CaseSeverity:
            count = len([c for c in self.cases.values() if c.severity == severity])
            severity_counts[severity.value] = count

        return {
            'total_cases': total_cases,
            'status_breakdown': status_counts,
            'severity_breakdown': severity_counts,
            'total_evidence': sum(len(c.evidence) for c in self.cases.values()),
            'total_notes': sum(len(c.notes) for c in self.cases.values())
        }
