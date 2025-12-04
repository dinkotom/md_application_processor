---
description: Deploy the application to PythonAnywhere
---

## Prerequisites

- A [PythonAnywhere](https://www.pythonanywhere.com/) account
- **Note**: Free tier does NOT support outbound connections (email fetching won't work). You need at least the **$5/month Hacker plan** for full functionality.
- Your GitHub repository URL
- Gmail credentials (app password)
- Google OAuth credentials (Client ID and Secret)

## Deployment Steps

### 1. Create Account
- Sign up for a PythonAnywhere account
- Upgrade to at least the **Hacker plan ($5/month)** if you need email fetching

### 2. Open Bash Console
- Go to the **Consoles** tab
- Click **Bash** to start a new console

### 3. Clone Repository
```bash
git clone https://github.com/yourusername/md_application_processor.git md_application_processor
cd md_application_processor
```
*Note: If your repo is private, you'll need to set up SSH keys or use a personal access token.*

### 4. Create Virtual Environment with Python 3.11
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
**Important**: Use `python3.11` specifically to match your local development version.

### 5. Initialize Databases
```bash
python3 << EOF
from web_app import init_db
init_db('applications.db')
init_db('applications_test.db')
print("Databases initialized successfully!")
EOF
```

### 6. Create Environment Variables
Create a `.env` file in your project directory:
```bash
nano .env
```

Add the following (replace with your actual values):
```
SECRET_KEY=your-production-secret-key-change-this
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-gmail-app-password
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
OAUTHLIB_INSECURE_TRANSPORT=0
```

**Important**: 
- `OAUTHLIB_INSECURE_TRANSPORT=0` for production (PythonAnywhere uses HTTPS)
- Generate a strong `SECRET_KEY` for production
- Use Gmail App Password, not your regular password

Save and exit (Ctrl+X, then Y, then Enter).

### 7. Configure Web App
- Go to the **Web** tab
- Click **Add a new web app**
- Choose **Manual configuration** (NOT the Flask wizard)
- Select **Python 3.11**

### 8. Set Virtual Environment Path
- In the **Web** tab, scroll to the **Virtualenv** section
- Enter: `/home/yourusername/md_application_processor/venv`
- Replace `yourusername` with your actual PythonAnywhere username
- Click the checkmark to save

### 9. Configure WSGI File
- In the **Web** tab, scroll to the **Code** section
- Click the link to edit the **WSGI configuration file** (e.g., `/var/www/yourusername_pythonanywhere_com_wsgi.py`)
- **Delete everything** in the file
- Add the following code (do NOT copy the ```python markers):

```python
import sys
import os
from dotenv import load_dotenv

# Add your project directory to the sys.path
project_home = '/home/yourusername/md_application_processor'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Load environment variables
load_dotenv(os.path.join(project_home, '.env'))

# Import flask app but need to call it "application" for WSGI to work
from web_app import app as application
```

**Important**: Replace `yourusername` with your actual PythonAnywhere username in the `project_home` path.

### 10. Reload and Test
- Go back to the **Web** tab
- Click the green **Reload** button at the top
- Visit your site at `yourusername.pythonanywhere.com`
- Test the login and email fetching features

## Updating the Application

When you push changes to GitHub, update your PythonAnywhere deployment:

```bash
cd ~/md_application_processor
git pull
```

Then go to the **Web** tab and click **Reload**.

## Troubleshooting

### "No module named 'authlib'" or similar import errors
- Make sure the virtualenv is set correctly in the **Web** tab
- Reinstall dependencies: `cd ~/md_application_processor && source venv/bin/activate && pip install -r requirements.txt`

### "Network is unreachable" when fetching emails
- You need a paid PythonAnywhere account (at least $5/month)
- Free tier blocks outbound connections

### Database errors
- Make sure you initialized the databases (step 5)
- Check that the database files exist: `ls -la ~/md_application_processor/*.db`

### OAuth errors
- Verify `OAUTHLIB_INSECURE_TRANSPORT=0` in your `.env` file
- Check that your Google OAuth redirect URI includes your PythonAnywhere URL

