from web_app import app

if __name__ == '__main__':
    print("Starting server without reloader...")
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)
