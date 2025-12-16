from flask import Blueprint, redirect, url_for, session, request
from src.extensions import oauth
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    """Login with Google"""
    redirect_uri = url_for('auth.authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/authorize')
def authorize():
    """Callback for Google OAuth"""
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
    
    # Store user info in session
    session['user'] = user_info
    
    # Check if user is admin (optional: based on email domain or specific list)
    # For now, allow all authenticated users
    
    return redirect(url_for('applicants.index'))

@auth_bp.route('/logout')
def logout():
    """Logout user"""
    session.pop('user', None)
    return redirect(url_for('applicants.index'))
