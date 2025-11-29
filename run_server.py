from web_app import app, init_db, DB_PATH_TEST, DB_PATH_PROD

if __name__ == '__main__':
    # Initialize databases (includes migrations)
    print("Initializing databases...")
    init_db(DB_PATH_TEST)
    init_db(DB_PATH_PROD)
    
    print("Starting server without reloader...")
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)
