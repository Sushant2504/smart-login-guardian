#!/usr/bin/env python3
"""
Smart Login Guardian - Production Web Application
Full-featured SaaS platform with authentication, database, and monitoring
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, g
from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

# Import configuration and models
from web.config.config import config
from web.database.models import db, User, LoginEvent, Alert
from web.routes.auth import auth_bp
from web.routes.main import main_bp
from web.middleware.auth import api_key_required

# Import Guardian
from guardian import LoginGuardian
from guardian.threat_intel import ThreatIntelligence
from guardian.analyzers.threat_intel_analyzer import ThreatIntelAnalyzer

# Initialize extensions
socketio = SocketIO()
login_manager = LoginManager()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
)


def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    login_manager.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])

    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Initialize Guardian
    guardian = LoginGuardian()
    threat_intel = ThreatIntelligence()
    threat_analyzer = ThreatIntelAnalyzer(threat_intel)
    guardian.analyzers.append(threat_analyzer)

    # Store in app context
    app.guardian = guardian
    app.threat_intel = threat_intel

    # API Routes for Guardian
    @app.route('/api/v1/analyze', methods=['POST'])
    @limiter.limit("100 per hour")
    @api_key_required
    def api_analyze():
        """Analyze login attempt via API"""
        data = request.json

        try:
            # Analyze with Guardian
            assessment = guardian.analyze_login(data)

            # Save to database
            event = LoginEvent(
                username=data.get('username'),
                ip_address=data.get('ip_address'),
                user_agent=data.get('user_agent'),
                country=data.get('location', {}).get('country') if data.get('location') else None,
                city=data.get('location', {}).get('city') if data.get('location') else None,
                latitude=data.get('location', {}).get('lat') if data.get('location') else None,
                longitude=data.get('location', {}).get('lon') if data.get('location') else None,
                success=data.get('success', False),
                risk_score=assessment.risk_score,
                risk_level=assessment.risk_level.value,
                signals=[s.__dict__ for s in assessment.signals],
                recommendation=assessment.recommendation,
                device_fingerprint=data.get('device_fingerprint'),
                session_id=data.get('session_id')
            )

            db.session.add(event)
            db.session.commit()

            # Create alert for high-risk events
            if assessment.risk_score >= 70:
                alert = Alert(
                    user_id=request.api_user.id,
                    title=f"High-risk login: {data.get('username')}",
                    description=f"Risk score {assessment.risk_score}: {assessment.recommendation}",
                    severity=assessment.risk_level.value,
                    event_id=event.id
                )
                db.session.add(alert)
                db.session.commit()

            # Broadcast to WebSocket clients
            socketio.emit('new_login', assessment.to_dict(), namespace='/')

            return assessment.to_dict(), 200

        except Exception as e:
            return {'error': str(e)}, 500

    @app.route('/api/v1/stats', methods=['GET'])
    @api_key_required
    def api_stats():
        """Get statistics"""
        total = LoginEvent.query.count()
        high_risk = LoginEvent.query.filter(LoginEvent.risk_score >= 60).count()
        critical = LoginEvent.query.filter(LoginEvent.risk_score >= 80).count()

        return {
            'total_events': total,
            'high_risk_count': high_risk,
            'critical_count': critical
        }

    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return {
            'status': 'healthy',
            'version': app.config['VERSION'],
            'timestamp': datetime.utcnow().isoformat()
        }

    # Request logging
    @app.before_request
    def before_request():
        g.start_time = datetime.utcnow()

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            elapsed = (datetime.utcnow() - g.start_time).total_seconds()
            response.headers['X-Response-Time'] = f'{elapsed:.3f}s'
        return response

    # Create database tables
    with app.app_context():
        db.create_all()

        # Create default admin user if doesn't exist
        admin = User.query.filter_by(email=app.config['ADMIN_EMAIL']).first()
        if not admin:
            admin = User(
                email=app.config['ADMIN_EMAIL'],
                username='admin',
                full_name='Administrator',
                role='admin',
                is_active=True,
                is_verified=True
            )
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Created admin user: {app.config['ADMIN_EMAIL']}")

    return app


if __name__ == '__main__':
    # Get environment
    env = os.environ.get('FLASK_ENV', 'development')

    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║         SMART LOGIN GUARDIAN - PRODUCTION SERVER                 ║
    ╚══════════════════════════════════════════════════════════════════╝

    Environment: {env}
    Dashboard:   http://localhost:5000
    API:         http://localhost:5000/api/v1
    Health:      http://localhost:5000/health

    Starting server...
    """.format(env=env.upper()))

    # Create app
    app = create_app(env)

    # Run with SocketIO
    socketio.run(
        app,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=(env == 'development')
    )
