# Welcome Email Template Documentation

## Overview
This template (`welcome_email.html`) is the official welcome email sent to new members of the Mladý divák club.

## Dynamic Fields

The following fields should be dynamically populated based on applicant information:

### 1. **First Name** (Greeting)
- **Location**: Line 177 in the main content section
- **Current**: `Ahoj<!-- DYNAMIC: {first_name} -->,`
- **Placeholder**: `{first_name}`
- **Example**: "Ahoj Tomáš," or "Ahoj Petra,"
- **Source**: `applicant_data['first_name']`

### 2. **Membership Card Attachment**
- **Not in HTML**: The membership card should be attached as a PNG file
- **Filename format**: `karta_{first_name}_{surname}_{membership_number}.png`
- **Source**: Generated using the existing card generation system

## Static Content (No Changes Needed)

The following content is static and does not need to be personalized:
- Logo and branding
- Welcome message ("Vítej v klubu Mladého diváka")
- All informational text about:
  - How the club works
  - Coordinators (Maruška and Zuzka)
  - Digital membership card benefits
  - Ticket purchasing process
  - Reservation policies
  - Social media links
- Footer with contact information
- Social media icons (Facebook, Instagram)

## Images Used

All images are hosted on Google Cloud Storage:
1. **Logo**: `https://storage.googleapis.com/mladydivakostrava54162/mlady%20divak-white.png`
2. **Card image**: `https://storage.googleapis.com/mladydivakostrava54162/ruka%20karta.png`

## Email Styling

- **Background color**: #F1F2F2 (light gray)
- **Main color**: #36378C (dark blue/purple)
- **Accent color**: #9EFF44 (lime green)
- **Secondary accent**: rgb(221, 49, 117) (pink)
- **Fonts**: 
  - Primary: Roboto (400, 700)
  - Secondary: Ubuntu (300, 400, 500, 700)
- **Max width**: 600px (standard email width)
- **Responsive**: Mobile-optimized with media queries

## Integration with Existing System

### Using with `src/email_sender.py`

The template can be integrated with the existing email sending system:

```python
from src.email_sender import send_email_with_card

# Read the template
with open('templates/welcome_email.html', 'r', encoding='utf-8') as f:
    html_template = f.read()

# Replace the placeholder
personalized_html = html_template.replace(
    'Ahoj<!-- DYNAMIC: {first_name} -->',
    f'Ahoj {applicant_data["first_name"]}'
)

# Send email with the card attachment
send_email_with_card(
    applicant_data=applicant_data,
    subject="Vítej v klubu Mladého diváka",
    body=personalized_html,
    card_image_bytes=card_bytes,
    email_user=email_user,
    email_pass=email_pass,
    mode='production'  # or 'test'
)
```

## Potential Future Enhancements

Consider adding these dynamic fields in the future:
1. **Membership number**: Could be displayed in the email body
2. **Expiration date**: When the membership expires
3. **Personalized event recommendations**: Based on age/interests
4. **Coordinator contact info**: Direct email/phone for Maruška and Zuzka
5. **Unsubscribe link**: Currently says "Klikněte zde" but has no actual link

## Notes

- The template uses MJML-style responsive email design
- Compatible with Outlook, Gmail, Apple Mail, and other major email clients
- Uses conditional comments for Outlook compatibility (`<!--[if mso | IE]>`)
- All external resources (images, fonts) are loaded from CDNs
- The template is in Czech language
