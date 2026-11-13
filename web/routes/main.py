"""
Main application routes
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from web.database.models import db, LoginEvent, Alert
from sqlalchemy import func, desc
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing page"""
    return render_template('index.html')


@main_bp.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html')


@main_bp.route('/features')
def features():
    """Features page"""
    return render_template('features.html')


@main_bp.route('/docs')
def docs():
    """Documentation page"""
    return render_template('docs.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main 3D dashboard"""
    return render_template('dashboard.html', user=current_user)


@main_bp.route('/admin')
@login_required
def admin():
    """Admin panel"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    return render_template('admin.html', user=current_user)


@main_bp.route('/profile')
@login_required
def profile():
    """User profile"""
    return render_template('profile.html', user=current_user)


@main_bp.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    """Get dashboard statistics"""
    # Time range filter
    hours = request.args.get('hours', 24, type=int)
    since = datetime.utcnow() - timedelta(hours=hours)

    # Total events
    total = LoginEvent.query.filter(LoginEvent.timestamp >= since).count()

    # Risk distribution
    risk_dist = db.session.query(
        LoginEvent.risk_level,
        func.count(LoginEvent.id)
    ).filter(
        LoginEvent.timestamp >= since
    ).group_by(LoginEvent.risk_level).all()

    risk_distribution = {level: count for level, count in risk_dist}

    # Success rate
    successful = LoginEvent.query.filter(
        LoginEvent.timestamp >= since,
        LoginEvent.success == True
    ).count()

    success_rate = (successful / total * 100) if total > 0 else 0

    # Top IPs
    top_ips = db.session.query(
        LoginEvent.ip_address,
        func.count(LoginEvent.id).label('count'),
        func.avg(LoginEvent.risk_score).label('avg_risk')
    ).filter(
        LoginEvent.timestamp >= since
    ).group_by(LoginEvent.ip_address).order_by(desc('count')).limit(10).all()

    # Top usernames
    top_users = db.session.query(
        LoginEvent.username,
        func.count(LoginEvent.id).label('count'),
        func.avg(LoginEvent.risk_score).label('avg_risk')
    ).filter(
        LoginEvent.timestamp >= since
    ).group_by(LoginEvent.username).order_by(desc('count')).limit(10).all()

    return jsonify({
        'total_events': total,
        'risk_distribution': risk_distribution,
        'success_rate': round(success_rate, 2),
        'high_risk_count': risk_distribution.get('high', 0) + risk_distribution.get('critical', 0),
        'critical_count': risk_distribution.get('critical', 0),
        'top_ips': [
            {'ip': ip, 'count': count, 'avg_risk': round(float(avg_risk), 2)}
            for ip, count, avg_risk in top_ips
        ],
        'top_usernames': [
            {'username': username, 'count': count, 'avg_risk': round(float(avg_risk), 2)}
            for username, count, avg_risk in top_users
        ],
        'time_range_hours': hours
    })


@main_bp.route('/api/events')
@login_required
def get_events():
    """Get login events"""
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    # Filters
    risk_level = request.args.get('risk_level')
    username = request.args.get('username')
    ip = request.args.get('ip')

    query = LoginEvent.query

    if risk_level:
        query = query.filter_by(risk_level=risk_level)
    if username:
        query = query.filter(LoginEvent.username.like(f'%{username}%'))
    if ip:
        query = query.filter_by(ip_address=ip)

    # Order by most recent
    query = query.order_by(LoginEvent.timestamp.desc())

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'events': [event.to_dict() for event in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })


@main_bp.route('/api/alerts')
@login_required
def get_alerts():
    """Get security alerts"""
    status = request.args.get('status', 'open')

    query = Alert.query.filter_by(user_id=current_user.id)

    if status != 'all':
        query = query.filter_by(status=status)

    alerts = query.order_by(Alert.created_at.desc()).limit(100).all()

    return jsonify({
        'alerts': [alert.to_dict() for alert in alerts]
    })


@main_bp.route('/api/alerts/<alert_id>', methods=['PATCH'])
@login_required
def update_alert(alert_id):
    """Update alert status"""
    alert = Alert.query.filter_by(id=alert_id, user_id=current_user.id).first()

    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    data = request.json
    status = data.get('status')

    if status not in ['open', 'investigating', 'resolved', 'false_positive']:
        return jsonify({'error': 'Invalid status'}), 400

    alert.status = status
    if status in ['resolved', 'false_positive']:
        alert.resolved_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        'message': 'Alert updated',
        'alert': alert.to_dict()
    })
