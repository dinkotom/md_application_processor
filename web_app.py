#!/usr/bin/env python3
"""
Web Dashboard for Application Processor
Displays applicant data from the database
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration
from flask import session

# Database configuration
DB_PATH_TEST = 'applications_test.db'
DB_PATH_PROD = 'applications.db'

VERSION = "1.0"

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
    return redirect(request.referrer or url_for('index'))

def calculate_age(dob_str):
    """Calculate age from DOB string (DD.MM.YYYY or DD/MM/YYYY)"""
    try:
        # Normalize separators
        clean_dob = dob_str.strip().replace('/', '.')
        dob = datetime.strptime(clean_dob, '%d.%m.%Y')
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
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

@app.route('/')
def index():
    """Main dashboard page"""
    conn = get_db_connection()
    
    # Get search and sort parameters
    search = request.args.get('search', '')
    filter_status = request.args.get('status', '')
    filter_age_group = request.args.get('age_group', '')
    filter_city = request.args.get('city', '')
    filter_school = request.args.get('school', '')
    filter_interest = request.args.get('interest', '')
    filter_source = request.args.get('source', '')
    sort_by = request.args.get('sort', 'id')  # Default sort by ID
    sort_order = request.args.get('order', 'desc')  # Default descending
    
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

    # Note: We can't filter city in SQL because SQLite's LOWER() doesn't handle Czech characters (Í, Ř, etc.)
    # We'll filter cities in Python after fetching

    # Note: We'll also filter schools in Python to apply normalization
    # This ensures filtering matches the grouping in stats

    if filter_source:
        query += " AND source = ?"
        params.append(filter_source)

    if filter_interest:
        query += " AND interests LIKE ?"
        params.append(f"%{filter_interest}%")

    # We need to fetch all to filter by age in python because age is calculated
    # But for efficiency, if no age filter, we can paginate in SQL.
    # However, since we calculate age on the fly, we can't easily filter by age in SQL unless we duplicate the logic or store DOB.
    # We store DOB. SQLite doesn't have easy date diff functions that match our python logic perfectly without extensions.
    # So we will fetch all matching other criteria, then filter by age in Python.
    
    cursor = conn.execute(query, params)
    all_applicants = [dict(row) for row in cursor.fetchall()]
    
    # Filter by city in Python (SQLite LOWER() doesn't handle Unicode properly)
    if filter_city:
        filtered_by_city = []
        for app in all_applicants:
            if app.get('city') and app['city'].strip().lower() == filter_city.lower():
                filtered_by_city.append(app)
        all_applicants = filtered_by_city
    
    # Filter by school in Python (to apply normalization that matches stats)
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

    # Sort by ID or application_received
    if sort_by == 'application_received':
        # Sort by application_received, handling NULL values (put them last)
        all_applicants.sort(
            key=lambda x: (x.get('application_received') is None, x.get('application_received') or ''),
            reverse=(sort_order == 'desc')
        )
    else:  # Default to ID
        all_applicants.sort(key=lambda x: x['id'], reverse=(sort_order == 'desc'))
    
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
        
        # Check for suspect duplicate
        from src.validator import is_suspect_duplicate
        app['suspect_duplicate'] = is_suspect_duplicate(
            app.get('first_name', ''), 
            app.get('last_name', ''), 
            app.get('email', ''), 
            db_path=get_db_path(),
            exclude_id=app.get('id')
        )
        final_applicants.append(app)
    
    conn.close()
    
    return render_template('index.html', 
                         applicants=final_applicants, 
                         search=search,
                         filter_status=filter_status,
                         filter_age_group=filter_age_group,
                         filter_city=filter_city,
                         filter_school=filter_school,
                         filter_interest=filter_interest,
                         filter_source=filter_source,
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
    
    # Check for suspect duplicate
    from src.validator import is_suspect_duplicate
    app_dict['suspect_duplicate'] = is_suspect_duplicate(
        app_dict.get('first_name', ''), 
        app_dict.get('last_name', ''), 
        app_dict.get('email', ''), 
        db_path=get_db_path(),
        exclude_id=app_dict.get('id')
    )
    
    return render_template('detail.html', applicant=app_dict)

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
    
    # Filename
    mid = app_dict.get('membership_id', '0000')
    safe_last = "".join([c for c in app_dict.get('last_name', '') if c.isalpha() or c.isdigit()]).rstrip()
    filename = f"prukaz_{mid}_{safe_last}.png"
    
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

@app.route('/advanced')
def advanced():
    """Advanced settings page"""
    return render_template('advanced.html')

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

@app.route('/applicant/<int:id>/export', methods=['POST'])
def export_applicant(id):
    """Export applicant to Ecomail"""
    from src.ecomail import export_to_ecomail
    from datetime import datetime
    
    conn = get_db_connection()
    applicant = conn.execute('SELECT * FROM applicants WHERE id = ? AND deleted = 0', (id,)).fetchone()
    
    if applicant is None:
        conn.close()
        return "Applicant not found", 404
    
    app_data = dict(applicant)
    
    # Call mocked Ecomail API
    result = export_to_ecomail(app_data)
    
    if result.get('success'):
        # Update database
        conn.execute('''
            UPDATE applicants 
            SET exported_to_ecomail = 1, exported_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), id))
        conn.commit()
    
    conn.close()
    
    # Redirect back to referrer or index
    referrer = request.referrer or url_for('index')
    return redirect(referrer)

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
        
        for row in rows:
            # Map CSV columns to database fields
            from src.parser import parse_csv_row
            data = parse_csv_row(row)
            
            record_applicant(data, db_path=get_db_path())
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        # Clear session
        session.pop('import_file', None)
        session.pop('import_stats', None)
    
    return redirect(url_for('index'))

@app.route('/clear_db', methods=['POST'])
def clear_database():
    """Clear database (Test mode only)"""
    mode = session.get('mode', 'test')
    
    if mode == 'production':
        # Protect production database
        return redirect(url_for('index'))
        
    # Clear test database
    conn = get_db_connection()
    conn.execute('DELETE FROM applicants')
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    print(f"Starting web dashboard...")
    print(f"Databases: {DB_PATH_TEST} / {DB_PATH_PROD}")
    print(f"Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
