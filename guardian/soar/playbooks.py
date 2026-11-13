"""
SOAR (Security Orchestration, Automation and Response) Playbooks
Automated response workflows for common security scenarios
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class PlaybookStatus(Enum):
    """Playbook execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class ActionStatus(Enum):
    """Individual action status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlaybookAction:
    """Individual action in a playbook"""
    action_id: str
    name: str
    action_type: str
    description: str
    parameters: Dict[str, Any]
    condition: Optional[str] = None
    timeout: int = 300  # 5 minutes default
    retry_count: int = 0
    max_retries: int = 3
    status: ActionStatus = ActionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_id': self.action_id,
            'name': self.name,
            'action_type': self.action_type,
            'description': self.description,
            'parameters': self.parameters,
            'condition': self.condition,
            'status': self.status.value,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error': self.error,
            'retry_count': self.retry_count
        }


@dataclass
class PlaybookExecution:
    """Playbook execution instance"""
    execution_id: str
    playbook_name: str
    trigger: str
    trigger_data: Dict[str, Any]
    status: PlaybookStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    actions: List[PlaybookAction] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'execution_id': self.execution_id,
            'playbook_name': self.playbook_name,
            'trigger': self.trigger,
            'trigger_data': self.trigger_data,
            'status': self.status.value,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'actions': [action.to_dict() for action in self.actions],
            'context': self.context,
            'logs': self.logs,
            'metrics': self.metrics
        }


class SOAREngine:
    """
    Security Orchestration, Automation and Response Engine
    Executes playbooks to automatically respond to security incidents
    """

    def __init__(self):
        self.playbooks: Dict[str, 'Playbook'] = {}
        self.executions: Dict[str, PlaybookExecution] = {}
        self.action_handlers: Dict[str, Callable] = {}
        self._register_default_actions()

    def _register_default_actions(self):
        """Register default action handlers"""
        self.register_action_handler('block_ip', self._block_ip_action)
        self.register_action_handler('disable_user', self._disable_user_action)
        self.register_action_handler('send_alert', self._send_alert_action)
        self.register_action_handler('create_ticket', self._create_ticket_action)
        self.register_action_handler('enrich_threat_intel', self._enrich_threat_intel_action)
        self.register_action_handler('quarantine_session', self._quarantine_session_action)
        self.register_action_handler('reset_password', self._reset_password_action)
        self.register_action_handler('log_event', self._log_event_action)
        self.register_action_handler('wait', self._wait_action)
        self.register_action_handler('webhook', self._webhook_action)

    def register_action_handler(self, action_type: str, handler: Callable):
        """Register a handler for an action type"""
        self.action_handlers[action_type] = handler

    def register_playbook(self, playbook: 'Playbook'):
        """Register a playbook"""
        self.playbooks[playbook.name] = playbook

    def execute_playbook(
        self,
        playbook_name: str,
        trigger: str,
        trigger_data: Dict[str, Any]
    ) -> PlaybookExecution:
        """Execute a playbook"""
        playbook = self.playbooks.get(playbook_name)
        if not playbook:
            raise ValueError(f"Playbook {playbook_name} not found")

        execution = PlaybookExecution(
            execution_id=str(uuid.uuid4()),
            playbook_name=playbook_name,
            trigger=trigger,
            trigger_data=trigger_data,
            status=PlaybookStatus.RUNNING,
            started_at=datetime.utcnow()
        )

        # Copy playbook actions
        for action_template in playbook.actions:
            action = PlaybookAction(
                action_id=str(uuid.uuid4()),
                name=action_template['name'],
                action_type=action_template['type'],
                description=action_template.get('description', ''),
                parameters=action_template.get('parameters', {}),
                condition=action_template.get('condition')
            )
            execution.actions.append(action)

        self.executions[execution.execution_id] = execution

        # Execute actions sequentially
        try:
            for action in execution.actions:
                self._execute_action(execution, action)

            execution.status = PlaybookStatus.COMPLETED
        except Exception as e:
            execution.status = PlaybookStatus.FAILED
            execution.logs.append(f"Playbook execution failed: {str(e)}")

        execution.completed_at = datetime.utcnow()
        return execution

    def _execute_action(self, execution: PlaybookExecution, action: PlaybookAction):
        """Execute a single action"""
        # Check condition
        if action.condition and not self._evaluate_condition(action.condition, execution.context):
            action.status = ActionStatus.SKIPPED
            execution.logs.append(f"Action {action.name} skipped due to condition")
            return

        action.status = ActionStatus.RUNNING
        action.started_at = datetime.utcnow()

        try:
            # Get handler
            handler = self.action_handlers.get(action.action_type)
            if not handler:
                raise ValueError(f"No handler for action type: {action.action_type}")

            # Execute with retry logic
            result = None
            while action.retry_count <= action.max_retries:
                try:
                    # Resolve parameters from context
                    resolved_params = self._resolve_parameters(action.parameters, execution.context)

                    # Execute handler
                    result = handler(resolved_params, execution.context)

                    action.status = ActionStatus.SUCCESS
                    action.result = result
                    execution.logs.append(f"Action {action.name} completed successfully")
                    break

                except Exception as e:
                    action.retry_count += 1
                    if action.retry_count > action.max_retries:
                        raise
                    execution.logs.append(
                        f"Action {action.name} failed (attempt {action.retry_count}/{action.max_retries}): {str(e)}"
                    )

            # Update context with result
            if result:
                execution.context[f"action_{action.action_id}_result"] = result

        except Exception as e:
            action.status = ActionStatus.FAILED
            action.error = str(e)
            execution.logs.append(f"Action {action.name} failed: {str(e)}")
            raise

        finally:
            action.completed_at = datetime.utcnow()

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition expression"""
        # Simple condition evaluation (can be enhanced with a proper expression parser)
        try:
            # Replace context variables
            for key, value in context.items():
                condition = condition.replace(f"${{{key}}}", str(value))

            # Evaluate
            return eval(condition)
        except Exception:
            return False

    def _resolve_parameters(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve parameter values from context"""
        resolved = {}
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                # Context variable reference
                var_name = value[2:-1]
                resolved[key] = context.get(var_name, value)
            else:
                resolved[key] = value
        return resolved

    # Default action handlers

    def _block_ip_action(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Block an IP address"""
        ip_address = params.get('ip_address')
        duration = params.get('duration', 3600)  # 1 hour default
        reason = params.get('reason', 'Automated block')

        # In production, this would integrate with firewall/WAF
        return {
            'action': 'block_ip',
            'ip_address': ip_address,
            'duration': duration,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }

    def _disable_user_action(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Disable a user account"""
        username = params.get('username')
        reason = params.get('reason', 'Security incident')

        # In production, this would integrate with identity provider
        return {
            'action': 'disable_user',
            'username': username,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }

    def _send_alert_action(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert notification"""
        channel = params.get('channel', 'email')
        recipients = params.get('recipients', [])
        message = params.get('message')
        severity = params.get('severity', 'medium')

        # In production, integrate with notification service
        return {
            'action': 'send_alert',
            'channel': channel,
            'recipients': recipients,
            'severity': severity,
            'sent_at': datetime.utcnow().isoformat()
        }

    def _create_ticket_action(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create incident ticket"""
        title = params.get('title')
        description = params.get('description')
        priority = params.get('priority', 'medium')
        assignee = params.get('assignee')

        # In production, integrate with ticketing system (Jira, ServiceNow, etc.)
        ticket_id = str(uuid.uuid4())[:8]

        return {
            'action': 'create_ticket',
            'ticket_id': ticket_id,
            'title': title,
            'priority': priority,
            'assignee': assignee,
            'created_at': datetime.utcnow().isoformat()
        }

    def _enrich_threat_intel_action(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich with threat intelligence"""
        indicator = params.get('indicator')
        indicator_type = params.get('indicator_type', 'ip')

        # In production, query threat intel sources
        return {
            'action': 'enrich_threat_intel',
            'indicator': indicator,
            'indicator_type': indicator_type,
            'threat_level': 'medium',
            'sources': ['local']
        }

    def _quarantine_session_action(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Quarantine a session"""
        session_id = params.get('session_id')

        return {
            'action': 'quarantine_session',
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        }

    def _reset_password_action(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Force password reset"""
        username = params.get('username')
        notify_user = params.get('notify_user', True)

        return {
            'action': 'reset_password',
            'username': username,
            'notify_user': notify_user,
            'timestamp': datetime.utcnow().isoformat()
        }

    def _log_event_action(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Log event"""
        message = params.get('message')
        level = params.get('level', 'info')

        return {
            'action': 'log_event',
            'message': message,
            'level': level,
            'timestamp': datetime.utcnow().isoformat()
        }

    def _wait_action(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Wait/sleep action"""
        import time
        duration = params.get('duration', 1)
        time.sleep(min(duration, 60))  # Cap at 60 seconds

        return {
            'action': 'wait',
            'duration': duration
        }

    def _webhook_action(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Send webhook"""
        url = params.get('url')
        method = params.get('method', 'POST')
        data = params.get('data', {})

        # In production, actually send the webhook
        return {
            'action': 'webhook',
            'url': url,
            'method': method,
            'sent_at': datetime.utcnow().isoformat()
        }

    def get_execution(self, execution_id: str) -> Optional[PlaybookExecution]:
        """Get playbook execution by ID"""
        return self.executions.get(execution_id)

    def get_playbook(self, name: str) -> Optional['Playbook']:
        """Get playbook by name"""
        return self.playbooks.get(name)


@dataclass
class Playbook:
    """Security playbook definition"""
    name: str
    description: str
    trigger_type: str  # manual, automatic, scheduled
    actions: List[Dict[str, Any]]
    enabled: bool = True
    tags: List[str] = field(default_factory=list)


# Default playbooks

BRUTE_FORCE_RESPONSE_PLAYBOOK = Playbook(
    name="brute_force_response",
    description="Automated response to brute force attacks",
    trigger_type="automatic",
    actions=[
        {
            'name': 'Block IP Address',
            'type': 'block_ip',
            'description': 'Block the attacking IP address',
            'parameters': {
                'ip_address': '${ip_address}',
                'duration': 3600,
                'reason': 'Brute force attack detected'
            }
        },
        {
            'name': 'Enrich Threat Intel',
            'type': 'enrich_threat_intel',
            'description': 'Gather threat intelligence on the IP',
            'parameters': {
                'indicator': '${ip_address}',
                'indicator_type': 'ip'
            }
        },
        {
            'name': 'Send Alert',
            'type': 'send_alert',
            'description': 'Alert security team',
            'parameters': {
                'channel': 'slack',
                'recipients': ['security-team'],
                'message': 'Brute force attack blocked from ${ip_address}',
                'severity': 'high'
            }
        },
        {
            'name': 'Create Incident',
            'type': 'create_ticket',
            'description': 'Create incident ticket',
            'parameters': {
                'title': 'Brute Force Attack - ${ip_address}',
                'description': 'Automated detection and response to brute force attack',
                'priority': 'high'
            }
        }
    ],
    tags=['brute_force', 'automated_response']
)

ACCOUNT_TAKEOVER_PLAYBOOK = Playbook(
    name="account_takeover_response",
    description="Response to suspected account takeover",
    trigger_type="automatic",
    actions=[
        {
            'name': 'Quarantine Session',
            'type': 'quarantine_session',
            'description': 'Quarantine the suspicious session',
            'parameters': {
                'session_id': '${session_id}'
            }
        },
        {
            'name': 'Disable User Account',
            'type': 'disable_user',
            'description': 'Temporarily disable the account',
            'parameters': {
                'username': '${username}',
                'reason': 'Suspected account takeover'
            }
        },
        {
            'name': 'Force Password Reset',
            'type': 'reset_password',
            'description': 'Force password reset',
            'parameters': {
                'username': '${username}',
                'notify_user': True
            }
        },
        {
            'name': 'Alert High Priority',
            'type': 'send_alert',
            'description': 'Send critical alert',
            'parameters': {
                'channel': 'pagerduty',
                'recipients': ['soc-oncall'],
                'message': 'CRITICAL: Account takeover detected for ${username}',
                'severity': 'critical'
            }
        },
        {
            'name': 'Create Investigation',
            'type': 'create_ticket',
            'description': 'Create investigation case',
            'parameters': {
                'title': 'Account Takeover Investigation - ${username}',
                'description': 'Automated response initiated. Full investigation required.',
                'priority': 'critical',
                'assignee': 'soc-lead'
            }
        }
    ],
    tags=['account_takeover', 'critical', 'automated_response']
)
