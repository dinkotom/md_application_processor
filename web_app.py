#!/usr/bin/env python3
"""
Web Dashboard for Application Processor
Displays applicant data from the database
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import logging

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

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration
from flask import session

# Database configuration
DB_PATH_TEST = 'applications_test.db'
DB_PATH_PROD = 'applications.db'

# Ecomail configuration
ECOMAIL_LIST_ID_TEST = 17
ECOMAIL_LIST_ID_PROD = 16

VERSION = "1.2"

def init_db(db_path):
    """Initialize database with schema if it doesn't exist"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create applicants table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applicants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            phone TEXT,
            dob TEXT,
            membership_id TEXT,
            city TEXT,
            school TEXT,
            interests TEXT,
            character TEXT,
            frequency TEXT,
            source TEXT,
            source_detail TEXT,
            message TEXT,
            color TEXT,
            newsletter INTEGER NOT NULL DEFAULT 1,
            full_body TEXT,
            status TEXT DEFAULT 'Nová',
            deleted INTEGER DEFAULT 0,
            exported_to_ecomail INTEGER DEFAULT 0,
            exported_at TIMESTAMP,
            application_received TIMESTAMP,
            email_sent INTEGER DEFAULT 0,
            email_sent_at TIMESTAMP,
            parent_email_warning_dismissed INTEGER DEFAULT 0,
            duplicate_warning_dismissed INTEGER DEFAULT 0,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(first_name, last_name, email)
        );
    ''')
    
    # Create email_template table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_template (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default email template if none exists
    cursor.execute('SELECT COUNT(*) FROM email_template')
    if cursor.fetchone()[0] == 0:
        default_subject = "Členská karta Mladý divák"
        default_body = """Dobrý den {first_name} {last_name},

děkujeme za Vaši přihlášku do programu Mladý divák.

V příloze naleznete Vaši členskou kartu (číslo {membership_id}).

S pozdravem,
Tým Mladý divák"""
        
        cursor.execute('''
            INSERT INTO email_template (subject, body)
            VALUES (?, ?)
        ''', (default_subject, default_body))
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized: {db_path}")

def get_db_path():
    """Get current database path based on session"""
    mode = session.get('mode', 'test')
    return DB_PATH_PROD if mode == 'production' else DB_PATH_TEST

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

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
    return redirect(request.referrer or url_for('index'))

def calculate_age(dob_str):
    """Calculate age from DOB string (DD.MM.YYYY or DD/MM/YYYY)"""
    try:
        # Normalize separators
        clean_dob = dob_str.strip().replace('/', '.')
        dob = datetime.strptime(clean_dob, '%d.%m.%Y')
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        # Return None for future dates or age 0 (invalid data)
        if age <= 0:
            return None
            
        return age
    except (ValueError, TypeError):
        return None

def normalize_school(school_name):
    """Normalize school names to group similar variations"""
    if not school_name:
        return school_name
    
    school = school_name.strip()
    school_lower = school.lower()
    
    # Define normalization rules
    # Format: (list of variations, canonical name)
    normalizations = [
        (['ostravská univerzita', 'osu'], 'Ostravská univerzita'),
        (['všb-tuo', 'všb'], 'VŠB-TUO'),
        # Add more normalizations here as needed
    ]
    
    for variations, canonical in normalizations:
        for variation in variations:
            if variation in school_lower:
                return canonical
    
    # If no normalization rule matches, return the original (stripped)
    return school

def slugify_status(status):
    """Convert status to CSS class friendly slug"""
    if not status:
        return 'nova'
    
    s = status.lower()
    replacements = {
        'á': 'a', 'č': 'c', 'ď': 'd', 'é': 'e', 'ě': 'e',
        'í': 'i', 'ň': 'n', 'ó': 'o', 'ř': 'r', 'š': 's',
        'ť': 't', 'ú': 'u', 'ů': 'u', 'ý': 'y', 'ž': 'z',
        ' ': '-'
    }
    
    for old, new in replacements.items():
        s = s.replace(old, new)
        
    return s

app.jinja_env.filters['slugify_status'] = slugify_status

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.png', mimetype='image/png')

def get_filtered_applicants(request_args):
    """Helper to get filtered and sorted applicants based on request args"""
    conn = get_db_connection()
    
    # Get search and sort parameters
    search = request_args.get('search', '')
    filter_status = request_args.get('status', '')
    filter_age_group = request_args.get('age_group', '')
    filter_city = request_args.get('city', '')
    filter_school = request_args.get('school', '')
    filter_interest = request_args.get('interest', '')
    filter_source = request_args.get('source', '')
    filter_alerts = request_args.get('alerts', '')  # New: filter for applicants with alerts
    sort_by = request_args.get('sort', 'id')  # Default sort by ID
    sort_order = request_args.get('order', 'desc')  # Default descending
    
    # Build query
    query = "SELECT * FROM applicants WHERE deleted = 0 AND 1=1"
    params = []
    
    if search:
        query += " AND (first_name LIKE ? OR last_name LIKE ? OR email LIKE ? OR city LIKE ?)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param, search_param])
    
    if filter_status:
        query += " AND status = ?"
        params.append(filter_status)

    if filter_source:
        query += " AND source = ?"
        params.append(filter_source)

    if filter_interest:
        query += " AND interests LIKE ?"
        params.append(f"%{filter_interest}%")

    cursor = conn.execute(query, params)
    all_applicants = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Filter by city in Python
    if filter_city:
        filtered_by_city = []
        for app in all_applicants:
            if app.get('city') and app['city'].strip().lower() == filter_city.lower():
                filtered_by_city.append(app)
        all_applicants = filtered_by_city
    
    # Filter by school in Python
    if filter_school:
        filtered_by_school = []
        for app in all_applicants:
            if app.get('school') and normalize_school(app['school']) == filter_school:
                filtered_by_school.append(app)
        all_applicants = filtered_by_school
    
    # Filter by age if requested
    if filter_age_group:
        filtered_applicants = []
        for app in all_applicants:
            age = calculate_age(app['dob']) if app['dob'] else None
            if age is not None:
                if filter_age_group == 'under_15' and age < 15:
                    filtered_applicants.append(app)
                elif filter_age_group == '15_18' and 15 <= age <= 18:
                    filtered_applicants.append(app)
                elif filter_age_group == '19_24' and 19 <= age <= 24:
                    filtered_applicants.append(app)
                elif filter_age_group == 'over_24' and age > 24:
                    filtered_applicants.append(app)
        all_applicants = filtered_applicants

    # Filter by alerts if requested
    if filter_alerts == 'true':
        from src.validator import is_suspect_parent_email
        filtered_by_alerts = []
        for app in all_applicants:
            has_alert = False
            
            # Check age warning
            age = calculate_age(app['dob']) if app['dob'] else None
            if age is None or age < 15 or age >= 25:
                has_alert = True
            
            # Check parent email warning (not dismissed)
            if not app.get('parent_email_warning_dismissed'):
                if is_suspect_parent_email(
                    app.get('first_name', ''),
                    app.get('last_name', ''),
                    app.get('email', '')
                ):
                    has_alert = True
            
            # Check duplicate warning (not dismissed)
            if not app.get('duplicate_warning_dismissed'):
                if app.get('is_duplicate'):
                    has_alert = True
            
            if has_alert:
                filtered_by_alerts.append(app)
        
        all_applicants = filtered_by_alerts

    # Sort by ID or application_received
    if sort_by == 'application_received':
        all_applicants.sort(
            key=lambda x: (x.get('application_received') is None, x.get('application_received') or ''),
            reverse=(sort_order == 'desc')
        )
    else:  # Default to ID (membership_id)
        all_applicants.sort(
            key=lambda x: (
                0 if str(x.get('membership_id', '')).isdigit() else 1, 
                int(x.get('membership_id')) if str(x.get('membership_id', '')).isdigit() else x.get('membership_id', '')
            ), 
            reverse=(sort_order == 'desc')
        )
    return all_applicants

@app.route('/')
def index():
    """Main dashboard page"""
    # Get filter parameters for template context
    search = request.args.get('search', '')
    filter_status = request.args.get('status', '')
    filter_age_group = request.args.get('age_group', '')
    filter_city = request.args.get('city', '')
    filter_school = request.args.get('school', '')
    filter_interest = request.args.get('interest', '')
    filter_source = request.args.get('source', '')
    filter_alerts = request.args.get('alerts', '')
    sort_by = request.args.get('sort', 'id')
    sort_order = request.args.get('order', 'desc')

    all_applicants = get_filtered_applicants(request.args)
    
    # Pagination (in memory now since we might filter by age)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    total_pages = (len(all_applicants) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    applicants_subset = all_applicants[start:end]
    
    # Calculate age for display (if not already done during filtering)
    # Note: If we filtered by age, 'age' key might not be set on the dict if we used the raw row.
    # Actually, in the age filtering loop, we calculated 'age' variable but didn't assign it back to 'app' dict unless we modify it.
    # Let's ensure all displayed applicants have 'age' set.
    
    final_applicants = []
    for app in applicants_subset:
        # app is a dict - always calculate age for display
        app['age'] = calculate_age(app['dob']) if app.get('dob') else None
        
        from src.validator import is_suspect_parent_email
        
        # Check for suspect parent email
        app['suspect_parent_email'] = (
            is_suspect_parent_email(
                app.get('first_name', ''),
                app.get('last_name', ''),
                app.get('email', '')
            ) and not app.get('parent_email_warning_dismissed', 0)
        )
        
        # Check for duplicate contact (email/phone)
        from src.validator import check_duplicate_contact
        duplicates = check_duplicate_contact(
            app.get('email', ''),
            app.get('phone', ''),
            current_id=app.get('id'),
            db_path=get_db_path()
        )
        
        app['is_duplicate'] = (
            (duplicates['email_duplicate'] or duplicates['phone_duplicate']) 
            and not app.get('duplicate_warning_dismissed', 0)
        )
        
        final_applicants.append(app)
    
    return render_template('index.html', 
                         applicants=final_applicants, 
                         search=search,
                         filter_status=filter_status,
                         filter_age_group=filter_age_group,
                         filter_city=filter_city,
                         filter_school=filter_school,
                         filter_interest=filter_interest,
                         filter_source=filter_source,
                         filter_alerts=filter_alerts,
                         page=page,
                         total_pages=total_pages,
                         total=len(all_applicants))
    
    # Calculate ages
    applicants_with_age = []
    for app in applicants:
        app_dict = dict(app)
        app_dict['age'] = calculate_age(app_dict.get('dob', '')) if app_dict.get('dob') else None
        applicants_with_age.append(app_dict)
    
    return render_template('index.html', 
                         applicants=applicants_with_age, 
                         search=search,
                         filter_status=filter_status,
                         total=len(applicants_with_age))

@app.route('/fetch/preview', methods=['POST'])
def fetch_preview():
    """Preview email applications and detect duplicates"""
    from src.fetcher import get_unread_emails
    from src.parser import parse_email_body
    from src.validator import is_duplicate
    import json
    import tempfile
    
    # Credentials
    email_user = os.environ.get("EMAIL_USER")
    email_pass = os.environ.get("EMAIL_PASS")
    
    if not email_user or not email_pass:
        return jsonify({'error': 'EMAIL_USER or EMAIL_PASS not set'}), 400
        
    try:
        # Fetch emails WITHOUT marking as read (preview only)
        emails = get_unread_emails(email_user, email_pass, mark_as_read=False)
        
        parsed_emails = []
        new_count = 0
        duplicate_count = 0
        
        for uid, body, email_date in emails:
            try:
                data = parse_email_body(body)
                data['_uid'] = uid
                data['_email_date'] = email_date  # Store email date for later
                
                # Check duplicate
                if is_duplicate(data.get('membership_id'), db_path=get_db_path()):
                    duplicate_count += 1
                else:
                    new_count += 1
                    parsed_emails.append(data)
                    
            except Exception as e:
                print(f"Error parsing email {uid}: {e}")
        
        # Store in temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump(parsed_emails, temp_file)
        temp_file.close()
        
        # Store in session
        session['fetch_file'] = temp_file.name
        session['fetch_stats'] = {
            'total': new_count + duplicate_count,
            'new': new_count,
            'duplicates': duplicate_count
        }
        
        return jsonify(session['fetch_stats'])
        
    except Exception as e:
        print(f"Fetch error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/fetch/confirm', methods=['POST'])
def fetch_confirm():
    """Confirm and execute email import"""
    from src.validator import record_applicant
    from src.fetcher import get_unread_emails
    import json
    
    if 'fetch_file' not in session:
        return redirect(url_for('index'))
    
    temp_file_path = session.get('fetch_file')
    
    try:
        # Read parsed emails from temp file
        with open(temp_file_path, 'r') as f:
            parsed_emails = json.load(f)
        
        # Import all non-duplicate emails
        from email.utils import parsedate_to_datetime
        
        for data in parsed_emails:
            # Convert email date to ISO format
            email_date_str = data.pop('_email_date', None)
            if email_date_str:
                try:
                    dt = parsedate_to_datetime(email_date_str)
                    data['application_received'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    data['application_received'] = None
            else:
                data['application_received'] = None
            
            # Remove the UID before recording (not part of applicant data)
            data.pop('_uid', None)
            record_applicant(data, db_path=get_db_path())
        
        # Now mark emails as read (only in production mode)
        mode = session.get('mode', 'test')
        if mode == 'production' and parsed_emails:
            email_user = os.environ.get("EMAIL_USER")
            email_pass = os.environ.get("EMAIL_PASS")
            
            if email_user and email_pass:
                # Re-fetch to mark as read
                # Note: This will mark ALL unread emails as read, including the duplicates
                # This is intentional - we don't want to process them again
                get_unread_emails(email_user, email_pass, mark_as_read=True)
        
    finally:
        # Clean up
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        session.pop('fetch_file', None)
        session.pop('fetch_stats', None)
    
    return redirect(url_for('index'))

@app.route('/applicant/<int:id>')
def applicant_detail(id):
    """Applicant detail page"""
    conn = get_db_connection()
    applicant = conn.execute('SELECT * FROM applicants WHERE id = ? AND deleted = 0', (id,)).fetchone()
    conn.close()
    
    if applicant is None:
        return "Applicant not found", 404
    
    app_dict = dict(applicant)
    app_dict['age'] = calculate_age(app_dict.get('dob', '')) if app_dict.get('dob') else None
    
    from src.validator import is_suspect_parent_email
    
    # Check for suspect parent email
    app_dict['suspect_parent_email'] = (
        is_suspect_parent_email(
            app_dict.get('first_name', ''),
            app_dict.get('last_name', ''),
            app_dict.get('email', '')
        ) and not app_dict.get('parent_email_warning_dismissed', 0)
    )
    
    # Check for duplicate contact (email/phone)
    from src.validator import check_duplicate_contact
    duplicates = check_duplicate_contact(
        app_dict.get('email', ''),
        app_dict.get('phone', ''),
        current_id=app_dict.get('id'),
        db_path=get_db_path()
    )
    
    app_dict['is_duplicate'] = (
        (duplicates['email_duplicate'] or duplicates['phone_duplicate']) 
        and not app_dict.get('duplicate_warning_dismissed', 0)
    )
    app_dict['duplicate_details'] = duplicates
    
    # Pass query parameters for the back button
    back_args = request.args.to_dict()
    
    # Find previous and next applicant IDs based on current filters/sort
    # We need to get the full list of applicants with current filters
    all_filtered = get_filtered_applicants(request.args)
    
    prev_id = None
    next_id = None
    
    # Find current applicant index
    current_index = -1
    for i, app in enumerate(all_filtered):
        if app['id'] == id:
            current_index = i
            break
            
    if current_index != -1:
        if current_index > 0:
            prev_id = all_filtered[current_index - 1]['id']
        if current_index < len(all_filtered) - 1:
            next_id = all_filtered[current_index + 1]['id']
    
    current_mode = session.get('mode', 'test')
    
    # Fetch Ecomail list names for confirmation dialog
    ecomail_list_name = None
    try:
        from src.ecomail import EcomailClient
        client = EcomailClient()
        lists_result = client.get_lists()
        
        if lists_result['success'] and lists_result['data']:
            # Get the appropriate list ID based on mode
            target_list_id = ECOMAIL_LIST_ID_TEST if current_mode == 'test' else ECOMAIL_LIST_ID_PROD
            
            # Find the list with matching ID
            for lst in lists_result['data']:
                if lst.get('id') == target_list_id:
                    ecomail_list_name = lst.get('name', f'List {target_list_id}')
                    break
            
            # Fallback if list not found
            if not ecomail_list_name:
                ecomail_list_name = f'List ID {target_list_id}'
    except Exception as e:
        logger.warning(f"Could not fetch Ecomail list names: {e}")
        # Fallback to showing just the ID
        target_list_id = ECOMAIL_LIST_ID_TEST if current_mode == 'test' else ECOMAIL_LIST_ID_PROD
        ecomail_list_name = f'List ID {target_list_id}'
    
    return render_template('detail.html', applicant=app_dict, back_args=back_args, prev_id=prev_id, next_id=next_id, current_mode=current_mode, ecomail_list_name=ecomail_list_name)

@app.route('/applicant/<int:id>/card')
def applicant_card(id):
    """Generate and serve membership card image"""
    from flask import send_file
    from src.generator import generate_membership_card
    import tempfile
    import os
    
    conn = get_db_connection()
    applicant = conn.execute('SELECT * FROM applicants WHERE id = ? AND deleted = 0', (id,)).fetchone()
    conn.close()
    
    if applicant is None:
        return "Applicant not found", 404
    
    app_dict = dict(applicant)
    
    # Generate card bytes
    img_io = generate_membership_card(app_dict)
    
    # Filename: id_name_surname without diacritics
    from src.generator import normalize_text
    mid = app_dict.get('membership_id', '0000')
    first_name = normalize_text(app_dict.get('first_name', '')).replace(' ', '_')
    last_name = normalize_text(app_dict.get('last_name', '')).replace(' ', '_')
    filename = f"{mid}_{first_name}_{last_name}.png"
    
    # Save to temporary file
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, filename)
    
    with open(temp_path, 'wb') as f:
        f.write(img_io.getvalue())
    
    # Send the file from disk
    return send_file(
        temp_path,
        mimetype='image/png',
        as_attachment=True,
        download_name=filename
    )

@app.route('/applicant/<int:id>/card_preview')
def serve_card_preview(id):
    """Generate and serve membership card preview (not as download)"""
    from flask import send_file
    from src.generator import generate_membership_card
    
    conn = get_db_connection()
    applicant = conn.execute('SELECT * FROM applicants WHERE id = ? AND deleted = 0', (id,)).fetchone()
    conn.close()
    
    if applicant is None:
        return "Applicant not found", 404
    
    app_dict = dict(applicant)
    
    # Generate card bytes
    img_io = generate_membership_card(app_dict)
    img_io.seek(0)
    
    # Send as inline image (not download)
    return send_file(img_io, mimetype='image/png')



@app.route('/stats')
def stats():
    """Statistics page"""
    conn = get_db_connection()
    
    # Get all applicants
    applicants = conn.execute('SELECT * FROM applicants WHERE deleted = 0').fetchall()
    
    # Calculate statistics
    total = len(applicants)
    
    ages = []
    cities = {}
    schools = {}
    interests_count = {}
    sources = {}
    
    for app in applicants:
        # Age distribution
        age = calculate_age(app['dob']) if app['dob'] else None
        if age is not None:
            ages.append(age)
        
        # City distribution
        if app['city']:
            city = app['city'].strip()
            # Capitalize first letter of each word for consistency (simple approach)
            # Or just use original case if we want to preserve it, but grouping requires normalization.
            # Let's use title case.
            city = city.title() 
            cities[city] = cities.get(city, 0) + 1
        
        # School distribution
        if app['school']:
            school = normalize_school(app['school'])
            schools[school] = schools.get(school, 0) + 1
        
        # Interests
        if app['interests']:
            for interest in app['interests'].split(','):
                interest = interest.strip()
                if interest:
                    interests_count[interest] = interests_count.get(interest, 0) + 1
        
        # Sources
        if app['source']:
            source = app['source'].strip()
            sources[source] = sources.get(source, 0) + 1
    
    # Age categories
    age_under_15 = len([a for a in ages if a < 15])
    age_15_18 = len([a for a in ages if 15 <= a <= 18])
    age_19_24 = len([a for a in ages if 19 <= a <= 24])
    age_over_24 = len([a for a in ages if a > 24])
    
    conn.close()
    
    return render_template('stats.html',
                         total=total,
                         age_under_15=age_under_15,
                         age_15_18=age_15_18,
                         age_19_24=age_19_24,
                         age_over_24=age_over_24,
                         cities=sorted(cities.items(), key=lambda x: x[1], reverse=True)[:10],
                         schools=sorted(schools.items(), key=lambda x: x[1], reverse=True)[:10],
                         interests=sorted(interests_count.items(), key=lambda x: x[1], reverse=True)[:10],
                         sources=sorted(sources.items(), key=lambda x: x[1], reverse=True))


@app.route('/exports')
def exports():
    """Exports page for CSV and other export functions"""
    return render_template('exports.html', 
                         version=VERSION, 
                         current_mode=session.get('mode', 'test'))

@app.route('/advanced')
def advanced():
    """Advanced settings page"""
    from src.ecomail import EcomailClient
    
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
    
    return render_template('advanced.html', 
                         ecomail_lists=ecomail_lists,
                         ecomail_error=ecomail_error)

# Soft delete endpoint
@app.route('/applicant/<int:id>/delete', methods=['POST'])
def delete_applicant(id):
    """Soft delete an applicant by setting deleted flag"""
    conn = get_db_connection()
    conn.execute('UPDATE applicants SET deleted = 1 WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/applicant/<int:id>/update', methods=['POST'])
def update_applicant(id):
    """Update applicant details"""
    conn = get_db_connection()
    
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    dob = request.form.get('dob')
    status = request.form.get('status')
    
    conn.execute('''
        UPDATE applicants 
        SET first_name = ?, last_name = ?, email = ?, phone = ?, dob = ?, status = ?
        WHERE id = ?
    ''', (first_name, last_name, email, phone, dob, status, id))
    
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/applicant/<int:id>/update_status', methods=['POST'])
def update_applicant_status(id):
    """Update applicant status only"""
    conn = get_db_connection()
    
    status = request.form.get('status')
    
    conn.execute('UPDATE applicants SET status = ? WHERE id = ?', (status, id))
    
    conn.commit()
    conn.close()
    
    # Redirect back to the same page (index)
    return redirect(url_for('index'))

@app.route('/applicant/<int:id>/update_field', methods=['POST'])
def update_applicant_field(id):
    """Update a single field of an applicant via AJAX"""
    data = request.get_json()
    field = data.get('field')
    value = data.get('value')
    
    allowed_fields = ['first_name', 'last_name', 'email', 'phone', 'dob', 'status']
    
    if field not in allowed_fields:
        return jsonify({'success': False, 'error': 'Invalid field'}), 400
        
    conn = get_db_connection()
    try:
        query = f'UPDATE applicants SET {field} = ? WHERE id = ?'
        conn.execute(query, (value, id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/applicant/<int:id>/update_note', methods=['POST'])
def update_applicant_note(id):
    """Update applicant note"""
    if request.is_json:
        data = request.get_json()
        note = data.get('note', '')
    else:
        note = request.form.get('note', '')
    
    conn = get_db_connection()
    try:
        conn.execute('UPDATE applicants SET note = ? WHERE id = ?', (note, id))
        conn.commit()
        logger.info(f"Updated note for applicant {id}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating note for applicant {id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/applicant/<int:id>/dismiss_parent_warning', methods=['POST'])
def dismiss_parent_warning(id):
    """Dismiss parent email warning for an applicant"""
    conn = get_db_connection()
    conn.execute('UPDATE applicants SET parent_email_warning_dismissed = 1 WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    logger.info(f"Dismissed parent email warning for applicant {id}")
    return redirect(url_for('applicant_detail', id=id))

@app.route('/applicant/<int:id>/dismiss_duplicate_warning', methods=['POST'])
def dismiss_duplicate_warning(id):
    """Dismiss duplicate contact warning for an applicant"""
    conn = get_db_connection()
    conn.execute('UPDATE applicants SET duplicate_warning_dismissed = 1 WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    logger.info(f"Dismissed duplicate warning for applicant {id}")
    return redirect(url_for('applicant_detail', id=id))

@app.route('/applicant/<int:id>/qr')
def qr_code(id):
    """Generate QR code on-the-fly for an applicant"""
    from flask import send_file
    from src.generator import generate_qr_code_bytes
    
    conn = get_db_connection()
    applicant = conn.execute('SELECT * FROM applicants WHERE id = ? AND deleted = 0', (id,)).fetchone()
    conn.close()
    
    if applicant is None:
        return "Applicant not found", 404
    
    app_data = dict(applicant)
    qr_bytes = generate_qr_code_bytes(app_data)
    
    return send_file(qr_bytes, mimetype='image/png')

@app.route('/applicant/<int:id>/export_to_ecomail', methods=['POST'])
def export_applicant_to_ecomail(id):
    """Export applicant to Ecomail"""
    from src.ecomail import EcomailClient
    from datetime import datetime
    
    conn = get_db_connection()
    applicant = conn.execute('SELECT * FROM applicants WHERE id = ? AND deleted = 0', (id,)).fetchone()
    
    if applicant is None:
        conn.close()
        return jsonify({'success': False, 'error': 'Applicant not found'}), 404
    
    app_data = dict(applicant)
    
    # Initialize Ecomail client
    try:
        client = EcomailClient()
        
        # Get list ID based on current mode (test or production)
        current_mode = session.get('mode', 'test')
        list_id = ECOMAIL_LIST_ID_TEST if current_mode == 'test' else ECOMAIL_LIST_ID_PROD
        
        logger.info(f"Using Ecomail list ID {list_id} for {current_mode} mode")

        # Prepare subscriber data
        # Parse interests into tags (comma-separated values)
        interests = app_data.get('interests', '')
        tags = [tag.strip() for tag in interests.split(',') if tag.strip()] if interests else []
        
        # Add character (Povaha) to tags if present
        character = app_data.get('character', '')
        if character:
            tags.append(character)
        
        # Add color (Barva) to tags if present
        color = app_data.get('color', '')
        if color:
            tags.append(color)
        
        # Convert DOB from DD/MM/YYYY or DD.MM.YYYY to YYYY-MM-DD for Ecomail
        dob_raw = app_data.get('dob', '')
        birthday = ''
        if dob_raw:
            try:
                # Handle both / and . as separators
                dob_parts = dob_raw.replace('.', '/').split('/')
                if len(dob_parts) == 3:
                    day, month, year = dob_parts
                    birthday = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except Exception as e:
                logger.warning(f"Could not parse DOB '{dob_raw}': {e}")
        
        subscriber_data = {
            'email': app_data['email'],
            'name': app_data['first_name'],
            'surname': app_data['last_name'],
            'phone': app_data.get('phone', ''),
            'city': app_data.get('city', ''),
            'birthday': birthday,
            'tags': tags,
            'custom_fields': {
                'CLENSKE_CISLO': str(app_data.get('membership_id', ''))
            }
        }
        
        logger.info(f"Exporting to Ecomail. City: '{app_data.get('city', '')}', DOB: '{app_data.get('dob', '')}', Tags: {subscriber_data['tags']}")
        logger.debug(f"Full subscriber data: {subscriber_data}")
        
        # Pass newsletter status (1=subscribed, 0=unsubscribed)
        newsletter_status = app_data.get('newsletter', 1)
        result = client.create_subscriber(list_id, subscriber_data, newsletter_status=newsletter_status)
        
        if result['success']:
            # Update database status
            conn.execute('''
                UPDATE applicants 
                SET exported_to_ecomail = 1, exported_at = ? 
                WHERE id = ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id))
            conn.commit()
            logger.info(f"Applicant {id} exported to Ecomail list {list_id} successfully.")
            conn.close()
            return jsonify({'success': True})
        else:
            logger.error(f"Failed to export applicant {id} to Ecomail: {result.get('error')}")
            conn.close()
            return jsonify({'success': False, 'error': result.get('error')}), 500
            
    except Exception as e:
        logger.error(f"Exception during Ecomail export: {str(e)}")
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ecomail/subscriber', methods=['POST'])
def lookup_subscriber():
    """Lookup subscriber in Ecomail"""
    from src.ecomail import EcomailClient
    
    email = request.form.get('email')
    if not email:
        return jsonify({'success': False, 'error': 'Email is required'}), 400
        
    try:
        client = EcomailClient()
        result = client.get_subscriber(email)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error looking up subscriber: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/import/preview', methods=['POST'])
def import_preview():
    """Preview CSV import and detect duplicates"""
    from flask import session
    import csv
    import io
    import json
    import tempfile
    from src.validator import is_duplicate
    
    if 'csv_file' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['csv_file']
    if file.filename == '':
        return redirect(url_for('index'))
    
    # Read CSV with utf-8-sig to handle BOM character
    stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
    csv_reader = csv.DictReader(stream)
    
    rows = []
    new_count = 0
    duplicate_count = 0
    
    for row in csv_reader:
        # Check for duplicates by CSV id (which maps to membership_id)
        csv_id = row.get('id', '').strip()
        exists = is_duplicate(csv_id, db_path=get_db_path())
        
        if exists:
            duplicate_count += 1
        else:
            new_count += 1
            rows.append(row)

    
    # Store in temporary file instead of session to avoid cookie size limits
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    json.dump(rows, temp_file)
    temp_file.close()
    
    # Store only the file path in session
    session['import_file'] = temp_file.name
    session['import_stats'] = {
        'total': new_count + duplicate_count,
        'new': new_count,
        'duplicates': duplicate_count
    }
    
    logger.info(f"CSV import preview: {new_count} new, {duplicate_count} duplicates.")
    return jsonify(session['import_stats'])

@app.route('/import/confirm', methods=['POST'])
def import_confirm():
    """Confirm and execute CSV import"""
    from flask import session
    from src.validator import record_applicant
    import json
    import os
    
    if 'import_file' not in session:
        return redirect(url_for('index'))
    
    # Read from temporary file
    temp_file_path = session.get('import_file')
    
    try:
        with open(temp_file_path, 'r') as f:
            rows = json.load(f)
        
        applicants = []
        for row in rows:
            # Map CSV columns to database fields
            from src.parser import parse_csv_row
            data = parse_csv_row(row)
            applicants.append(data)
            
        # Import all applicants
        for app_data in applicants:
            record_applicant(app_data, db_path=get_db_path())
        
        logger.info(f"Imported {len(applicants)} applicants from CSV")
        
        return jsonify({
            'success': True, 
            'message': f'Úspěšně importováno {len(applicants)} uchazečů',
            'count': len(applicants)
        })
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        # Clear session
        session.pop('import_file', None)
        session.pop('import_stats', None)

@app.route('/clear_db', methods=['POST'])
def clear_database():
    """Clear database (Test mode only)"""
    mode = session.get('mode', 'test')
    
    if mode == 'production':
        # Protect production database
        logger.warning("Attempted to clear database in production mode. Action blocked.")
        return redirect(url_for('index'))
        
    # Clear test database
    conn = get_db_connection()
    conn.execute('DELETE FROM applicants')
    conn.commit()
    conn.close()
    logger.info("Test database cleared.")
    
    return redirect(url_for('index'))

@app.route('/email/template', methods=['GET'])
def get_email_template():
    """Get current email template"""
    conn = get_db_connection()
    template = conn.execute('SELECT subject, body FROM email_template ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    
    if template:
        return jsonify({
            'subject': template['subject'],
            'body': template['body']
        })
    else:
        return jsonify({
            'subject': '',
            'body': ''
        })

@app.route('/email/template', methods=['POST'])
def save_email_template():
    """Save email template"""
    subject = request.form.get('subject', '')
    body = request.form.get('body', '')
    
    conn = get_db_connection()
    
    # Update or insert template
    conn.execute('''
        INSERT INTO email_template (subject, body, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    ''', (subject, body))
    
    conn.commit()
    conn.close()
    logger.info("Email template saved.")
    
    return jsonify({'success': True, 'message': 'Template saved successfully'})

@app.route('/applicant/<int:id>/email/preview', methods=['POST'])
def preview_email(id):
    """Preview email for applicant"""
    from src.email_sender import preview_email as generate_preview
    
    conn = get_db_connection()
    applicant = conn.execute('SELECT * FROM applicants WHERE id = ? AND deleted = 0', (id,)).fetchone()
    template = conn.execute('SELECT subject, body FROM email_template ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    
    if not applicant:
        return jsonify({'error': 'Applicant not found'}), 404
    
    if not template:
        return jsonify({'error': 'Email template not configured'}), 400
    
    app_data = dict(applicant)
    mode = session.get('mode', 'test')
    
    preview = generate_preview(app_data, template['subject'], template['body'], mode)
    
    return jsonify(preview)

@app.route('/applicant/<int:id>/email/send', methods=['POST'])
def send_email(id):
    """Send email with membership card to applicant"""
    from src.email_sender import send_email_with_card
    from src.generator import generate_membership_card
    
    conn = get_db_connection()
    applicant = conn.execute('SELECT * FROM applicants WHERE id = ? AND deleted = 0', (id,)).fetchone()
    template = conn.execute('SELECT subject, body FROM email_template ORDER BY id DESC LIMIT 1').fetchone()
    
    if not applicant:
        conn.close()
        return jsonify({'error': 'Applicant not found'}), 404
    
    if not template:
        conn.close()
        return jsonify({'error': 'Email template not configured'}), 400
    
    app_data = dict(applicant)
    mode = session.get('mode', 'test')
    
    # Generate membership card
    card_bytes = generate_membership_card(app_data)
    
    # Get email credentials
    email_user = os.environ.get('EMAIL_USER')
    email_pass = os.environ.get('EMAIL_PASS')
    
    if not email_user or not email_pass:
        conn.close()
        return jsonify({'error': 'Email credentials not configured'}), 500
    
    # Send email
    result = send_email_with_card(
        app_data,
        template['subject'],
        template['body'],
        card_bytes,
        email_user,
        email_pass,
        mode
    )
    
    if result['success']:
        # Update database
        conn.execute('''
            UPDATE applicants 
            SET email_sent = 1, email_sent_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (id,))
        conn.commit()
    
    conn.close()
    
    return jsonify(result)

@app.route('/changelog')
def get_changelog():
    """Get changelog content"""
    from src.changelog import get_changelog as read_changelog
    import markdown
    
    changelog_md = read_changelog()
    changelog_html = markdown.markdown(changelog_md, extensions=['fenced_code', 'tables'])
    
    return jsonify({'content': changelog_html})

@app.route('/export/csv')
def export_csv():
    """Export applicants to CSV file"""
    import csv
    import io
    from flask import make_response
    
    # Get status filter from query params
    status_filter = request.args.get('status', '')
    
    # Get all applicants from database
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if status_filter:
        cursor.execute('SELECT * FROM applicants WHERE deleted = 0 AND status = ? ORDER BY id DESC', (status_filter,))
    else:
        cursor.execute('SELECT * FROM applicants WHERE deleted = 0 ORDER BY id DESC')
    
    applicants = cursor.fetchall()
    conn.close()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Jméno', 'Příjmení', 'Email', 'Telefon', 'Datum narození',
        'Členské číslo', 'Město', 'Škola', 'Zájmy', 'Povaha', 'Frekvence',
        'Zdroj', 'Detail zdroje', 'Vzkaz', 'Barva', 'Newsletter', 'Status',
        'Vytvořeno', 'Přihláška přijata'
    ])
    
    # Write data rows
    for app in applicants:
        writer.writerow([
            app['id'],
            app['first_name'],
            app['last_name'],
            app['email'],
            app['phone'],
            app['dob'],
            app['membership_id'],
            app['city'],
            app['school'],
            app['interests'],
            app['character'],
            app['frequency'],
            app['source'],
            app['source_detail'],
            app['message'],
            app['color'],
            'Ano' if app['newsletter'] == 1 else 'Ne',
            app['status'],
            app['created_at'],
            app.get('application_received', '')
        ])
    
    # Create response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=prihlasky_{status_filter if status_filter else "vsechny"}.csv'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    
    return response

@app.route('/exports/ecomail/lists')
def get_ecomail_lists_for_export():
    """Get Ecomail lists for bulk export dropdown"""
    from src.ecomail import EcomailClient
    
    try:
        client = EcomailClient()
        result = client.get_lists()
        
        if result['success']:
            return jsonify({
                'success': True,
                'lists': result.get('data', [])
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to fetch lists')
            })
    except Exception as e:
        logger.error(f"Error fetching Ecomail lists for export: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/exports/ecomail/bulk', methods=['POST'])
def bulk_export_to_ecomail():
    """Bulk export applicants to Ecomail"""
    from src.ecomail import EcomailClient
    
    try:
        data = request.get_json()
        list_id = data.get('list_id')
        
        if not list_id:
            return jsonify({'success': False, 'error': 'List ID is required'})
        
        # Get all applicants (not deleted)
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM applicants WHERE deleted = 0 ORDER BY id DESC')
        
        applicants = cursor.fetchall()
        conn.close()
        
        if not applicants:
            return jsonify({
                'success': False,
                'error': 'Žádné přihlášky k exportu'
            })
        
        # Initialize Ecomail client
        client = EcomailClient()
        
        created_count = 0
        updated_count = 0
        error_count = 0
        
        # Export each applicant
        for app in applicants:
            try:
                # Prepare subscriber data
                tags = []
                if app['interests']:
                    # Split by comma and strip whitespace
                    interest_tags = [i.strip() for i in app['interests'].split(',')]
                    # Ensure no commas remain in individual tags (replace with hyphen if any)
                    interest_tags = [t.replace(',', ' -') for t in interest_tags if t]
                    tags.extend(interest_tags)
                if app['source']:
                    # Replace comma with hyphen in source tag
                    source_val = app['source'].replace(',', ' -')
                    tags.append(f"Zdroj: {source_val}")
                
                # Final safety check: remove any remaining commas from all tags
                tags = [t.replace(',', ' -') for t in tags]
                
                subscriber_data = {
                    'email': app['email'],
                    'name': f"{app['first_name']} {app['last_name']}",
                    'surname': app['last_name'],
                    'vokativ': app['first_name'],
                    'tags': tags
                }
                
                # Add custom fields if present
                if app['membership_id']:
                    subscriber_data['CLENSKE_CISLO'] = app['membership_id']
                if app['city']:
                    subscriber_data['city'] = app['city']
                if app['phone']:
                    subscriber_data['phone'] = app['phone']
                
                # Check if subscriber exists
                existing = client.get_subscriber(app['email'])
                is_update = existing.get('success') and existing.get('data')
                
                # For new subscribers, use their newsletter consent from database
                # For existing subscribers, pass None to preserve their current status
                newsletter_status_param = None if is_update else (app['newsletter'] if app['newsletter'] is not None else 1)
                
                # Create/update subscriber
                result = client.create_subscriber(
                    list_id, 
                    subscriber_data, 
                    newsletter_status=newsletter_status_param
                )
                
                if result['success']:
                    if is_update:
                        updated_count += 1
                    else:
                        created_count += 1
                else:
                    error_count += 1
                    logger.warning(f"Failed to export applicant {app['id']}: {result.get('error')}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error exporting applicant {app['id']}: {e}")
        
        return jsonify({
            'success': True,
            'created': created_count,
            'updated': updated_count,
            'errors': error_count,
            'total': len(applicants)
        })
        
    except Exception as e:
        logger.error(f"Bulk export error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    # Initialize databases
    init_db(DB_PATH_TEST)
    init_db(DB_PATH_PROD)
    
    print(f"Starting web dashboard...")
    print(f"Databases: {DB_PATH_TEST} / {DB_PATH_PROD}")
    print(f"Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
