---
description: Deploy the application to PythonAnywhere
---

1.  **Create Account**:
    -   Sign up for a [PythonAnywhere](https://www.pythonanywhere.com/) account (Beginner account is free).

2.  **Open Console**:
    -   Go to the **Consoles** tab and start a new **Bash** console.

3.  **Clone Repository**:
    -   Clone your code: `git clone <your-github-repo-url> mysite`
    -   *Note: If your repo is private, you'll need to set up SSH keys or use a token.*

4.  **Setup Virtual Environment**:
    -   Go into the directory: `cd mysite`
    -   Create virtualenv: `python3 -m venv venv`
    -   Activate it: `source venv/bin/activate`
    -   Install requirements: `pip install -r requirements.txt`

5.  **Configure Web App**:
    -   Go to the **Web** tab.
    -   Click **Add a new web app**.
    -   Choose **Manual configuration** (not Flask wizard) -> select **Python 3.11** (or matching your local version).

6.  **Configure WSGI**:
    -   In the **Web** tab, scroll down to the **Code** section.
    -   Click the link to edit the **WSGI configuration file** (e.g., `/var/www/yourusername_pythonanywhere_com_wsgi.py`).
    -   Delete everything and add the following code (do **NOT** copy the \`\`\`python lines, just the code inside):
        ```python
        import sys
        import os
        from dotenv import load_dotenv

        # Add your project directory to the sys.path
        project_home = '/home/yourusername/mysite'
        if project_home not in sys.path:
            sys.path = [project_home] + sys.path

        # Load environment variables
        load_dotenv(os.path.join(project_home, '.env'))

        # Import flask app but need to call it "application" for WSGI to work
        from web_app import app as application
        ```
    -   *Replace `yourusername` with your actual PythonAnywhere username.*

7.  **Environment Variables**:
    -   Create a `.env` file in your project folder on PythonAnywhere (`/home/yourusername/mysite/.env`) with your production secrets:
        ```
        SECRET_KEY=your-production-secret-key
        EMAIL_USER=your-email@gmail.com
        EMAIL_PASS=your-app-password
        GOOGLE_CLIENT_ID=...
        GOOGLE_CLIENT_SECRET=...
        OAUTHLIB_INSECURE_TRANSPORT=0  # Ensure this is 0 for production!
        ```

8.  **Reload**:
    -   Go back to the **Web** tab and click the green **Reload** button at the top.
    -   Visit your site at `yourusername.pythonanywhere.com`.
