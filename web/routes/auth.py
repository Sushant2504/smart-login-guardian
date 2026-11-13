"""
Authentication routes
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from web.database.models import db, User, APIKey
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        if request.is_json:
            data = request.json
        else:
            data = request.form

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            if request.is_json:
                return jsonify({'error': 'Email and password required'}), 400
            flash('Email and password required', 'error')
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_active:
                if request.is_json:
                    return jsonify({'error': 'Account is disabled'}), 403
                flash('Account is disabled', 'error')
                return render_template('login.html')

            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            db.session.commit()

            if request.is_json:
                return jsonify({
                    'message': 'Login successful',
                    'user': user.to_dict()
                })

            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))

        if request.is_json:
            return jsonify({'error': 'Invalid credentials'}), 401
        flash('Invalid email or password', 'error')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        if request.is_json:
            data = request.json
        else:
            data = request.form

        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        full_name = data.get('full_name')
        company = data.get('company')

        # Validation
        if not email or not username or not password:
            if request.is_json:
                return jsonify({'error': 'Email, username, and password required'}), 400
            flash('All fields are required', 'error')
            return render_template('register.html')

        # Check if user exists
        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({'error': 'Email already registered'}), 400
            flash('Email already registered', 'error')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({'error': 'Username already taken'}), 400
            flash('Username already taken', 'error')
            return render_template('register.html')

        # Create user
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            company=company,
            role='user'
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Auto login
        login_user(user)

        if request.is_json:
            return jsonify({
                'message': 'Registration successful',
                'user': user.to_dict()
            }), 201

        flash('Registration successful! Welcome to Smart Login Guardian.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/api/keys', methods=['GET', 'POST'])
@login_required
def api_keys():
    """Manage API keys"""
    if request.method == 'POST':
        data = request.json
        name = data.get('name')

        if not name:
            return jsonify({'error': 'Name required'}), 400

        # Create API key
        api_key = APIKey(
            user_id=current_user.id,
            name=name,
            key=APIKey.generate_key()
        )

        db.session.add(api_key)
        db.session.commit()

        # Return full key only on creation
        return jsonify({
            'message': 'API key created',
            'api_key': {
                'id': api_key.id,
                'name': api_key.name,
                'key': api_key.key,  # Full key shown only once
                'created_at': api_key.created_at.isoformat()
            }
        }), 201

    # GET: List user's API keys
    keys = APIKey.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'api_keys': [key.to_dict() for key in keys]
    })


@auth_bp.route('/api/keys/<key_id>', methods=['DELETE'])
@login_required
def delete_api_key(key_id):
    """Delete API key"""
    api_key = APIKey.query.filter_by(id=key_id, user_id=current_user.id).first()

    if not api_key:
        return jsonify({'error': 'API key not found'}), 404

    db.session.delete(api_key)
    db.session.commit()

    return jsonify({'message': 'API key deleted'})
