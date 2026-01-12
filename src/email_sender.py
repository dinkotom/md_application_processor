#!/usr/bin/env python3
"""
Email sender module for sending membership cards
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
import os


def render_email_template(template_text, applicant_data):
    """
    Replace placeholders in email template with applicant data
    
    Args:
        template_text: Email template with {placeholders}
        applicant_data: Dict with applicant information
    
    Returns:
        Rendered email text
    """
    replacements = {
        '{first_name}': applicant_data.get('first_name', ''),
        '{last_name}': applicant_data.get('last_name', ''),
        '{membership_id}': applicant_data.get('membership_id', ''),
        '{email}': applicant_data.get('email', ''),
    }
    
    result = template_text
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, str(value))
    
    return result


def render_html_email_template(template_html, applicant_data):
    """
    Replace dynamic content in HTML email template with applicant data
    
    Args:
        template_html: HTML email template
        applicant_data: Dict with applicant information
    
    Returns:
        Rendered HTML email
    """
    result = template_html
    
    # Template no longer uses dynamic content replacement for name
    pass
    
    return result


def load_welcome_email_template(root_path=None):
    """
    Load the welcome email HTML template
    
    Args:
        root_path: Optional root path to search for templates
        
    Returns:
        tuple: (HTML template string, path_used) - content is None if not found
    """
    if root_path:
        template_path = os.path.join(root_path, 'templates', 'welcome_email.html')
    else:
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'templates',
            'welcome_email.html'
        )
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read(), template_path
    except FileNotFoundError:
        print(f"Warning: Welcome email template not found at {template_path}")
        return None, template_path


def get_recipient_email(applicant_email, mode):
    """
    Get the actual recipient email based on mode
    
    Args:
        applicant_email: The applicant's email address
        mode: 'test' or 'production'
    
    Returns:
        Email address to send to
    """
    if mode == 'test':
        return 'u7745030724@gmail.com'
    return applicant_email


def send_email_with_card(applicant_data, subject, body, card_image_bytes, email_user, email_pass, mode='test', use_html=False, copy_to=None, smtp_host='smtp.gmail.com', smtp_port=465):
    """
    Send email with membership card attachment
    
    Args:
        applicant_data: Dict with applicant information
        subject: Email subject (can contain placeholders)
        body: Email body (can contain placeholders) or HTML template
        card_image_bytes: BytesIO object with PNG image
        email_user: SMTP username
        email_pass: SMTP password
        mode: 'test' or 'production'
        use_html: If True, treat body as HTML content
        copy_to: Optional email address to copy (CC) - mainly for test mode
        smtp_host: SMTP server hostname (default: smtp.gmail.com)
        smtp_port: SMTP server port (default: 465)
    
    Returns:
        Dict with success status and message
    """
    try:
        # Render email content
        rendered_subject = render_email_template(subject, applicant_data)
        
        if use_html:
            rendered_body = render_html_email_template(body, applicant_data)
        else:
            rendered_body = render_email_template(body, applicant_data)
        
        # Get recipient
        recipient = get_recipient_email(applicant_data.get('email'), mode)
        
        # In test mode, append copy_to if provided
        to_header = recipient
        if mode == 'test' and copy_to:
            to_header = f"{recipient}, {copy_to}"
        
        # Create message
        msg = MIMEMultipart()
        # Use friendly sender name
        msg['From'] = "Mladý divák <info@mladydivak.cz>"
        msg['Reply-To'] = "info@mladydivak.cz"
        msg['To'] = to_header
        msg['Subject'] = rendered_subject
        
        # Add body (HTML or plain text)
        if use_html:
            msg.attach(MIMEText(rendered_body, 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(rendered_body, 'plain', 'utf-8'))
        
        # Filename: id_name_surname without diacritics
        first_name = render_email_template('{first_name}', applicant_data).lower().replace(' ', '_')
        last_name = render_email_template('{last_name}', applicant_data).lower().replace(' ', '_')
        mid = applicant_data.get('membership_id', '0000')
        
        # Remove diacritics
        import unicodedata
        first_name = ''.join(c for c in unicodedata.normalize('NFD', first_name) if unicodedata.category(c) != 'Mn')
        last_name = ''.join(c for c in unicodedata.normalize('NFD', last_name) if unicodedata.category(c) != 'Mn')
        
        attachment_filename = f"{mid}_{first_name}_{last_name}.png"
        
        card_image_bytes.seek(0)
        image = MIMEImage(card_image_bytes.read(), name=attachment_filename)
        image.add_header('Content-Disposition', 'attachment', filename=attachment_filename)
        msg.attach(image)
        
        # Send email via SMTP
        if int(smtp_port) == 587 or int(smtp_port) == 25:
            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                server.starttls()
                server.login(email_user, email_pass)
                server.send_message(msg)
        else:
            with smtplib.SMTP_SSL(smtp_host, int(smtp_port)) as server:
                server.login(email_user, email_pass)
                server.send_message(msg)
            
        print(f"DEBUG: Email sent via SMTP to {to_header} from {email_user}")
        
        return {
            'success': True,
            'message': f'Email sent successfully to {to_header}',
            'recipient': to_header
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to send email: {str(e)}',
            'error': str(e)
        }


def send_welcome_email(applicant_data, card_image_bytes, email_user, email_pass, mode='test', copy_to=None, smtp_host='smtp.gmail.com', smtp_port=465):
    """
    Send welcome email using the official HTML template
    
    Args:
        applicant_data: Dict with applicant information
        card_image_bytes: BytesIO object with PNG image
        email_user: SMTP username
        email_pass: SMTP password
        mode: 'test' or 'production'
        copy_to: Optional email address to receive copy in test mode
        smtp_host: SMTP server hostname (default: smtp.gmail.com)
        smtp_port: SMTP server port (default: 465)
    
    Returns:
        Dict with success status and message
    """
    # Load the welcome email template
    html_template, _ = load_welcome_email_template()
    
    if html_template is None:
        return {
            'success': False,
            'message': 'Welcome email template not found',
            'error': 'Template file missing'
        }
    
    # Send email with HTML template
    return send_email_with_card(
        applicant_data=applicant_data,
        subject="Vítej v klubu Mladého diváka",
        body=html_template,
        card_image_bytes=card_image_bytes,
        email_user=email_user,
        email_pass=email_pass,
        mode=mode,
        use_html=True,
        copy_to=copy_to,
        smtp_host=smtp_host,
        smtp_port=smtp_port
    )


def preview_email(applicant_data, subject, body, mode='test'):
    """
    Generate email preview without sending
    
    Args:
        applicant_data: Dict with applicant information
        subject: Email subject template
        body: Email body template
        mode: 'test' or 'production'
    
    Returns:
        Dict with preview data
    """
    rendered_subject = render_email_template(subject, applicant_data)
    rendered_body = render_email_template(body, applicant_data)
    recipient = get_recipient_email(applicant_data.get('email'), mode)
    
    return {
        'recipient': recipient,
        'subject': rendered_subject,
        'body': rendered_body,
        'mode': mode,
        'is_test_mode': mode == 'test'
    }
