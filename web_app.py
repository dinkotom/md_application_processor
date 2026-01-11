#!/usr/bin/env python3
"""
Web Dashboard for Application Processor
Displays applicant data from the database
"""

from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory
import os
from dotenv import load_dotenv
import logging
from src.extensions import oauth

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Version
VERSION = '2.0.0'

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Allow OAuth over HTTP for development (set to '0' in production with HTTPS)
    if 'OAUTHLIB_INSECURE_TRANSPORT' not in os.environ:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = os.getenv('OAUTHLIB_INSECURE_TRANSPORT', '1')

    # Session configuration
    app.config.update(
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )
    
    # Initialize Extensions
    oauth.init_app(app)
    # Register Google OAuth here or in auth blueprint? Authlib registers on the oauth object.
    # We need to register the remote app on the oauth object.
    oauth.register(
        name='google',
        client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.applicants import applicants_bp
    from routes.settings import settings_bp
    
    app.register_blueprint(auth_bp) # Register at root to match Google Console redirect URI
    app.register_blueprint(applicants_bp) # Register at root for index
    app.register_blueprint(settings_bp)

    # Context Processors & Shared Filters
    @app.context_processor
    def inject_mode():
        """Inject current mode into templates"""
        return dict(current_mode=session.get('mode', 'test'), version=VERSION)
    
    @app.route('/switch_mode/<mode>')
    def switch_mode(mode):
        """Switch between test and production mode"""
        if mode in ['test', 'production']:
            session['mode'] = mode
            logger.info(f"Switched to {mode} mode")
        return redirect(request.referrer or url_for('applicants.index'))

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.png', mimetype='image/png')
                                   
    from src.parser import datetime_cz, datetime_cz_minutes, slugify_status
    app.jinja_env.filters['datetime_cz'] = datetime_cz
    app.jinja_env.filters['datetime_cz_minutes'] = datetime_cz_minutes
    app.jinja_env.filters['slugify_status'] = slugify_status
    
    return app

app = create_app()

if __name__ == '__main__':
    # Initialize DB (optional check)
    from src.database import init_db, DB_PATH_TEST
    init_db(DB_PATH_TEST)
    
    app.run(debug=True, port=8000)
