from src.email_sender import load_welcome_email_template, render_html_email_template

# Mock data
applicant_data = {
    'first_name': 'Jan',
    'last_name': 'Novák',
    'membership_id': '12345',
    'email': 'jan.novak@example.com'
}

# Load
print("Loading template...")
html = load_welcome_email_template()

if html:
    # Render
    print("Rendering template...")
    rendered = render_html_email_template(html, applicant_data)
    
    # Extract the greeting part to show what happened
    start_idx = rendered.find("Ahoj")
    end_idx = rendered.find("vítáme tě")
    
    print("\n--- RENDERED OUTPUT SNIPPET (Greeting) ---")
    if start_idx != -1:
        snippet = rendered[start_idx:end_idx+20]
        print(snippet.strip())
    else:
        print("Greeting 'Ahoj' not found in template.")
        
    print("\n--- FULL OUTPUT LENGTH ---")
    print(f"Total characters: {len(rendered)}")
else:
    print("Failed to load template.")
