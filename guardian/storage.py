from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
from pathlib import Path

from .models import LoginAttempt, UserProfile


class LoginStorage:
    """In-memory storage for login history and user profiles"""

    def __init__(self, persistence_path: Optional[str] = None):
        self.login_history: List[LoginAttempt] = []
        self.user_profiles: Dict[str, UserProfile] = {}
        self.ip_history: Dict[str, List[LoginAttempt]] = defaultdict(list)
        self.persistence_path = persistence_path

        if persistence_path:
            self._load_from_disk()

    def add_login_attempt(self, attempt: LoginAttempt):
        """Record a login attempt"""
        self.login_history.append(attempt)
        self.ip_history[attempt.ip_address].append(attempt)

        # Update or create user profile
        if attempt.username not in self.user_profiles:
            self.user_profiles[attempt.username] = UserProfile(username=attempt.username)

        profile = self.user_profiles[attempt.username]
        profile.last_login = attempt
        profile.last_updated = datetime.utcnow()
        profile.total_logins += 1

        if not attempt.success:
            profile.failed_attempts_count += 1
        else:
            # Reset failed attempts on successful login
            profile.failed_attempts_count = 0

            # Update usual patterns
            if attempt.location and attempt.location not in profile.usual_locations:
                profile.usual_locations.append(attempt.location)

            if attempt.ip_address not in profile.usual_ips:
                profile.usual_ips.append(attempt.ip_address)
                # Keep only last 10 IPs
                if len(profile.usual_ips) > 10:
                    profile.usual_ips.pop(0)

            if attempt.device_fingerprint and attempt.device_fingerprint not in profile.usual_devices:
                profile.usual_devices.append(attempt.device_fingerprint)

            hour = attempt.timestamp.hour
            if hour not in profile.usual_login_hours:
                profile.usual_login_hours.append(hour)

    def get_user_profile(self, username: str) -> Optional[UserProfile]:
        """Get user profile by username"""
        return self.user_profiles.get(username)

    def get_recent_attempts(self, username: str, minutes: int = 60) -> List[LoginAttempt]:
        """Get recent login attempts for a user"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [
            attempt for attempt in self.login_history
            if attempt.username == username and attempt.timestamp >= cutoff
        ]

    def get_recent_failed_attempts(self, username: str, minutes: int = 30) -> List[LoginAttempt]:
        """Get recent failed login attempts for a user"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [
            attempt for attempt in self.login_history
            if attempt.username == username
            and not attempt.success
            and attempt.timestamp >= cutoff
        ]

    def get_ip_attempts(self, ip_address: str, minutes: int = 60) -> List[LoginAttempt]:
        """Get recent attempts from an IP address"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [
            attempt for attempt in self.ip_history.get(ip_address, [])
            if attempt.timestamp >= cutoff
        ]

    def get_unique_usernames_from_ip(self, ip_address: str, minutes: int = 60) -> set:
        """Get unique usernames attempted from an IP (account enumeration detection)"""
        attempts = self.get_ip_attempts(ip_address, minutes)
        return {attempt.username for attempt in attempts}

    def cleanup_old_entries(self, days: int = 30):
        """Remove login attempts older than specified days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        self.login_history = [
            attempt for attempt in self.login_history
            if attempt.timestamp >= cutoff
        ]

        # Rebuild IP history
        self.ip_history = defaultdict(list)
        for attempt in self.login_history:
            self.ip_history[attempt.ip_address].append(attempt)

    def _load_from_disk(self):
        """Load persisted data from disk"""
        path = Path(self.persistence_path)
        if not path.exists():
            return

        try:
            with open(path, 'r') as f:
                data = json.load(f)
                # Implementation for deserialization would go here
        except Exception as e:
            print(f"Error loading from disk: {e}")

    def _save_to_disk(self):
        """Save data to disk"""
        if not self.persistence_path:
            return

        path = Path(self.persistence_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, 'w') as f:
                # Implementation for serialization would go here
                pass
        except Exception as e:
            print(f"Error saving to disk: {e}")
