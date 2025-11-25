import imaplib
import email
from email.header import decode_header
from typing import List, Tuple

def get_unread_emails(username: str, password: str, imap_server: str = "imap.gmail.com", mark_as_read: bool = False) -> List[Tuple[str, str]]:
    """
    Connects to IMAP and retrieves unread emails.
    
    Args:
        username: Email username
        password: Email password
        imap_server: IMAP server address
        mark_as_read: If True, mark emails as read after fetching (production mode)
    
    Returns:
        List of tuples (email_uid, email_body_text)
    """
    mail = imaplib.IMAP4_SSL(imap_server)
    try:
        mail.login(username, password)
        mail.select("inbox")
        
        # Search for all unread emails
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            return []
            
        email_ids = messages[0].split()
        results = []
        
        for e_id in email_ids:
            # Fetch the email header first to check subject
            # Use BODY.PEEK[HEADER] to avoid marking as read if we don't process it
            res, header_data = mail.fetch(e_id, '(BODY.PEEK[HEADER])')
            
            subject_matched = False
            for response_part in header_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    
                    if "Nová Přihláška" in subject:
                        subject_matched = True
                        break
            
            if subject_matched:
                # Fetch the full body
                if mark_as_read:
                    # Use BODY[] to mark as read (production mode)
                    res, msg_data = mail.fetch(e_id, "(BODY[])")
                else:
                    # Use BODY.PEEK[] to keep unread (test mode)
                    res, msg_data = mail.fetch(e_id, "(BODY.PEEK[])")
                    
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Extract body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                
                                if "attachment" not in content_disposition:
                                    if content_type == "text/plain":
                                        body = part.get_payload(decode=True).decode()
                                        break # Prefer plain text
                                    elif content_type == "text/html":
                                        # Fallback to HTML if no plain text found yet
                                        if not body:
                                            body = part.get_payload(decode=True).decode()
                        else:
                            body = msg.get_payload(decode=True).decode()
                            
                        results.append((e_id.decode(), body))
        
        return results
                    
        return results
        
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return []
    finally:
        try:
            mail.close()
            mail.logout()
        except:
            pass

if __name__ == "__main__":
    # Test with dummy credentials (will fail but checks syntax)
    print("Fetcher module loaded. Run from main.py with real credentials.")
