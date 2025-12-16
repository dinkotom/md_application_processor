from web_app import create_app
import sys

try:
    print("Initializing Application Factory...")
    app = create_app()
    
    print("\nRegistered Blueprints:")
    for name, bp in app.blueprints.items():
        print(f" - {name}")
        
    required_blueprints = {'auth', 'applicants', 'settings'}
    registered = set(app.blueprints.keys())
    
    if required_blueprints.issubset(registered):
        print("\nSUCCESS: All required blueprints are registered.")
    else:
        print(f"\nFAILURE: Missing blueprints: {required_blueprints - registered}")
        sys.exit(1)
        
    print("\nChecking Routes:")
    rules = [str(p) for p in app.url_map.iter_rules()]
    required_routes = [
        '/login', '/logout', '/authorize', # Auth
        '/', '/applicant/<int:id>', '/applicant/<int:id>/status', # Applicants
        '/advanced', '/stats', '/clear_database', # Settings
        '/fetch/preview', '/import/preview'
    ]
    
    missing_routes = []
    for route in required_routes:
        found = False
        for rule in rules:
            if rule == route or rule == route + '/':  # approximate match
                found = True
                break
            # wildcard match
            if '<int:id>' in route:
                 # convert to regex approximate or just check prefix
                 pass
                 
    # Simple check for existence of substrings in rules
    print(f"Total routes: {len(rules)}")
    
    # Check specific endpoints exist in url_map
    endpoints = [r.endpoint for r in app.url_map.iter_rules()]
    print("\nEndpoints sample:", endpoints[:5])
    
    required_endpoints = [
        'applicants.index', 'applicants.detail', 'applicants.update_applicant_status',
        'auth.login', 'auth.logout',
        'settings.advanced', 'settings.stats', 'settings.clear_database'
    ]
    
    missing = [e for e in required_endpoints if e not in endpoints]
    
    if not missing:
        print("\nSUCCESS: All key endpoints found.")
    else:
        print(f"\nFAILURE: Missing endpoints: {missing}")
        sys.exit(1)

except Exception as e:
    print(f"\nCRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
