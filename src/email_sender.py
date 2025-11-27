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


def send_email_with_card(applicant_data, subject, body, card_image_bytes, email_user, email_pass, mode='test'):
    """
    Send email with membership card attachment
    
    Args:
        applicant_data: Dict with applicant information
        subject: Email subject (can contain placeholders)
        body: Email body (can contain placeholders)
        card_image_bytes: BytesIO object with PNG image
        email_user: SMTP username
        email_pass: SMTP password
        mode: 'test' or 'production'
    
    Returns:
        Dict with success status and message
    """
    try:
        # Render email content
        rendered_subject = render_email_template(subject, applicant_data)
        rendered_body = render_email_template(body, applicant_data)
        
        # Get recipient
        recipient = get_recipient_email(applicant_data.get('email'), mode)
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = "info@mladydivak.cz"
        msg['Reply-To'] = "info@mladydivak.cz"
        msg['To'] = recipient
        msg['Subject'] = rendered_subject
        
        # Add body
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
        
        # Send email via Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(email_user, email_pass)
            server.send_message(msg)
        
        return {
            'success': True,
            'message': f'Email sent successfully to {recipient}',
            'recipient': recipient
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to send email: {str(e)}',
            'error': str(e)
        }


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
