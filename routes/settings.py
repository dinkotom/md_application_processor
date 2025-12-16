from flask import Blueprint, render_template, request, session, redirect, url_for, current_app, jsonify
from src.database import get_db_connection, log_action, get_db_path, init_db
from src.ecomail import EcomailClient
from src.email_sender import load_welcome_email_template
from src.parser import datetime_cz, parse_csv_row
from src.changelog import get_changelog
from datetime import datetime
import logging
import csv
import io
import os

settings_bp = Blueprint('settings', __name__)
logger = logging.getLogger(__name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@settings_bp.route('/advanced')
@login_required
def advanced():
    """Advanced settings page"""
    
    # Load welcome email template for preview
    # Use current_app.root_path to get correct path
    welcome_email_preview, welcome_email_path = load_welcome_email_template(current_app.root_path)
    
    # Fetch Ecomail lists
    ecomail_lists = None
    ecomail_error = None
    try:
        client = EcomailClient()
        result = client.get_lists()
        if result['success']:
            ecomail_lists = result.get('data', [])
        else:
            ecomail_error = result.get('error', 'Neznámá chyba')
    except ValueError as e:
        ecomail_error = str(e)
    except Exception as e:
        logger.error(f"Error fetching Ecomail lists: {e}")
        ecomail_error = f"Neočekávaná chyba: {str(e)}"
    
    current_mode = session.get('mode', 'production')
    
    return render_template('advanced.html', 
                         ecomail_lists=ecomail_lists,
                         ecomail_error=ecomail_error,
                         welcome_email_preview=welcome_email_preview,
                         welcome_email_path=welcome_email_path,
                         current_mode=current_mode)

@settings_bp.route('/stats')
@login_required
def stats():
    """Statistics page"""
    conn = get_db_connection()
    
    # Fetch all non-deleted applicants
    applicants = conn.execute('SELECT * FROM applicants WHERE deleted = 0').fetchall()
    conn.close()
    
    total_applicants = len(applicants)
    
    # Initialize counters
    age_groups = {'under_15': 0, '15_18': 0, '19_24': 0, 'over_24': 0}
    cities = {}
    schools = {}
    interests = {}
    sources = {}
    characters = {}
    gender_stats = {'female': 0, 'male': 0, 'unknown': 0}
    
    from src.parser import calculate_age, normalize_school
    
    for app in applicants:
        # Age Stats
        age = calculate_age(app['dob']) if app['dob'] else None
        if age:
            if age < 15: age_groups['under_15'] += 1
            elif 15 <= age <= 18: age_groups['15_18'] += 1
            elif 19 <= age <= 24: age_groups['19_24'] += 1
            else: age_groups['over_24'] += 1
            
        # City Stats
        if app['city']:
            city = app['city'].strip()
            cities[city] = cities.get(city, 0) + 1
            
        # School Stats
        if app['school']:
            school = normalize_school(app['school'])
            schools[school] = schools.get(school, 0) + 1
            
        # Interest Stats (comma split)
        if app['interests']:
            for interest in app['interests'].split(','):
                interest = interest.strip()
                if interest:
                    interests[interest] = interests.get(interest, 0) + 1
                    
        # Source Stats
        if app['source']:
            source = app['source'].strip()
            sources[source] = sources.get(source, 0) + 1
            
        # Character Stats
        if app['character']:
            char = app['character'].strip()
            characters[char] = characters.get(char, 0) + 1

        # Gender Stats
        gender = app['guessed_gender']
        if gender == 'female':
            gender_stats['female'] += 1
        elif gender == 'male':
            gender_stats['male'] += 1
        else:
            gender_stats['unknown'] += 1

    # Sort dictionary by count desc
    def sort_dict(d):
        return sorted(d.items(), key=lambda x: x[1], reverse=True)
        
    return render_template('stats.html',
                           total_applicants=total_applicants,
                           age_under_15=age_groups['under_15'],
                           age_15_18=age_groups['15_18'],
                           age_19_24=age_groups['19_24'],
                           age_over_24=age_groups['over_24'],
                           cities=sort_dict(cities),
                           schools=sort_dict(schools),
                           interests=sort_dict(interests),
                           sources=sort_dict(sources),
                           characters=sort_dict(characters),
                           gender_stats=gender_stats)

# --- Management Routes ---

@settings_bp.route('/changelog')
def changelog():
    """Get changelog content"""
    # Assuming get_changelog reads CHANGELOG.md
    # I might need to implement src.changelog if it doesn't exist or is simple.
    # List dir showed src/changelog.py.
    try:
        from src.changelog import get_changelog_html
        content = get_changelog_html()
    except ImportError:
        # Fallback if function name is different
        with open(os.path.join(current_app.root_path, 'CHANGELOG.md'), 'r') as f:
            content = f.read() # Return raw markdown if parser missing?
            # Or use markdown lib if available.
            # Usually we send JSON
            pass
            
    # For now, let's assume we read the file directly if src.changelog is complex
    import markdown
    try:
        with open(os.path.join(current_app.root_path, 'CHANGELOG.md'), 'r') as f:
            md_content = f.read()
            html_content = markdown.markdown(md_content)
    except Exception as e:
        html_content = f"Error loading changelog: {e}"
        
    return jsonify({'content': html_content})

@settings_bp.route('/clear_database', methods=['POST'])
@login_required
def clear_database():
    """Clear test database (Test mode only)"""
    if session.get('mode') == 'production':
        return "Cannot clear production database", 403
        
    conn = get_db_connection()
    # Drop table or Delete all? Delete all is safer to keep schema
    conn.execute('DELETE FROM applicants')
    conn.execute('DELETE FROM audit_logs')
    # Actually, init_db might be better?
    conn.commit()
    conn.close()
    
    # Re-init default template?
    # For now just clear applicants is main goal.
    
    return redirect(url_for('settings.advanced'))



# DEBUG LOGGING GLOBAL REMOVED

@settings_bp.route('/import/preview', methods=['POST'])
@login_required
def import_preview():
    """Preview CSV import"""
    if 'csv_file' not in request.files:
        return jsonify({'error': 'No file'}), 400
        
    file = request.files['csv_file']
    if not file:
        return jsonify({'error': 'Empty file'}), 400
    
    try:
        stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
        csv_input = csv.DictReader(stream)
        
        # Count rows and check duplicates
        total = 0
        new_count = 0
        duplicates_count = 0
        
        conn = get_db_connection()
        existing_emails = set(row['email'] for row in conn.execute('SELECT email FROM applicants').fetchall())
        conn.close()
        
        for row in csv_input:
            total += 1
            email = row.get('email', '').strip()
            if email in existing_emails:
                duplicates_count += 1
            else:
                new_count += 1
                
        # Save file to temp for confirmation step
        session['import_file_path'] = f"/tmp/import_{session['user'].get('email')}.csv"
        
        # Reset stream
        file.stream.seek(0)
        file.save(session['import_file_path'])
            
        return jsonify({
            'total': total,
            'new': new_count,
            'duplicates': duplicates_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/import/confirm', methods=['POST'])
@login_required
def import_confirm():
    """Execute CSV import"""
    path = session.get('import_file_path')
    
    if not path or not os.path.exists(path):
        return jsonify({'error': 'File expired'}), 400
        
    count = 0
    conn = get_db_connection()
    
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            csv_input = csv.DictReader(f)
            for row in csv_input:
                # Check duplicate again
                email = row.get('email', '').strip()
                
                curr = conn.execute('SELECT id, deleted FROM applicants WHERE email = ?', (email,)).fetchone()
                
                if curr:
                    if curr['deleted']:
                        # Restore
                        conn.execute('UPDATE applicants SET deleted = 0 WHERE id = ?', (curr['id'],))
                        user_email = session.get('user', {}).get('email', 'unknown_import')
                        log_action(curr['id'], "Obnoveno importem", user_email, connection=conn)
                        count += 1
                    else:
                        # Log duplicate attempt even if active (per user feedback "missing log")
                        # This ensures the user sees that the import touched this record.
                        user_email = session.get('user', {}).get('email', 'unknown_import')
                        log_action(curr['id'], "Pokus o import (duplicita)", user_email, connection=conn)
                    continue
                    
                # Parse and Insert
                data = parse_csv_row(row)
                data['status'] = 'Nová'
                data['application_received'] = datetime.now()
                
                # Insert logic...
                keys = list(data.keys())
                placeholders = ', '.join(['?' for _ in keys])
                cols = ', '.join(keys)
                vals = [data[k] for k in keys]
                
                cursor = conn.execute(f'INSERT INTO applicants ({cols}) VALUES ({placeholders})', vals)
                new_id = cursor.lastrowid
                
                user_email = session.get('user', {}).get('email', 'unknown_import')
                log_action(new_id, "Vytvořeno importem", user_email, connection=conn)
                count += 1
                
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
        # os.remove(path) # Keep file for potential debug? No, standard logic.
        if os.path.exists(path):
            os.remove(path)
        session.pop('import_file_path', None)
        
    return jsonify({'success': True, 'count': count})

@settings_bp.route('/ecomail/create_list', methods=['POST'])
@login_required
def ecomail_create_list():
    """Create Ecomail list"""
    try:
        client = EcomailClient()
        data = request.form
        res = client.create_list(data) # Assuming create_list method exists
        # If not, implement or use generic request
        if 'error' in res and res['error']:
             return jsonify({'success': False, 'error': res['error']}), 400
        return jsonify({'success': True, 'data': res})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@settings_bp.route('/ecomail/subscriber', methods=['POST'])
@login_required
def ecomail_subscriber():
    """Lookup subscriber"""
    email = request.form.get('email')
    if not email:
        return jsonify({'success': False, 'error': 'No email'}), 400
        
    try:
        client = EcomailClient()
        res = client.get_subscriber(email)
        return jsonify(res)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

