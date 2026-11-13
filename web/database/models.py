"""
Database models for production application
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User account model"""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Profile
    full_name = db.Column(db.String(120))
    company = db.Column(db.String(120))
    role = db.Column(db.String(20), default='user')  # user, admin, viewer

    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    api_keys = db.relationship('APIKey', back_populates='user', cascade='all, delete-orphan')
    alerts = db.relationship('Alert', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name,
            'company': self.company,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class APIKey(db.Model):
    """API key for programmatic access"""
    __tablename__ = 'api_keys'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    name = db.Column(db.String(120), nullable=False)
    key = db.Column(db.String(64), unique=True, nullable=False, index=True)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)

    # Relationships
    user = db.relationship('User', back_populates='api_keys')

    @staticmethod
    def generate_key():
        """Generate a new API key"""
        return str(uuid.uuid4()) + str(uuid.uuid4()).replace('-', '')

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'key': self.key[:8] + '...' + self.key[-4:],  # Masked
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class LoginEvent(db.Model):
    """Login event storage"""
    __tablename__ = 'login_events'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Login details
    username = db.Column(db.String(120), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    user_agent = db.Column(db.Text)

    # Location
    country = db.Column(db.String(2))
    city = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    # Result
    success = db.Column(db.Boolean, default=False)
    risk_score = db.Column(db.Integer, default=0, index=True)
    risk_level = db.Column(db.String(20), index=True)

    # Signals
    signals = db.Column(db.JSON)
    recommendation = db.Column(db.Text)

    # Metadata
    device_fingerprint = db.Column(db.String(64))
    session_id = db.Column(db.String(64))

    # Timestamps
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'location': {
                'country': self.country,
                'city': self.city,
                'lat': self.latitude,
                'lon': self.longitude
            } if self.country else None,
            'success': self.success,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'signals': self.signals or [],
            'recommendation': self.recommendation,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Alert(db.Model):
    """Security alert"""
    __tablename__ = 'alerts'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # Alert details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(20), nullable=False)  # low, medium, high, critical

    # Status
    status = db.Column(db.String(20), default='open')  # open, investigating, resolved, false_positive

    # Related event
    event_id = db.Column(db.String(36))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resolved_at = db.Column(db.DateTime)

    # Relationships
    user = db.relationship('User', back_populates='alerts')

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'status': self.status,
            'event_id': self.event_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


class Setting(db.Model):
    """Application settings"""
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_value(key, default=None):
        """Get setting value"""
        setting = Setting.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set_value(key, value, description=None):
        """Set setting value"""
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            setting = Setting(key=key, value=value, description=description)
            db.session.add(setting)
        db.session.commit()
        return setting
