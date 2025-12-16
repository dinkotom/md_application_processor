import qrcode
from PIL import Image, ImageDraw, ImageFont

from typing import Dict
import os

def generate_qr_code(data: Dict[str, str], output_path: str) -> str:
    """
    Generates a QR code image from the application data.
    Payload format: First|Last|DOB|Email|MembershipID
    """
    # Construct payload
    payload = (
        f"Jméno: {data.get('first_name', '')}\n"
        f"Příjmení: {data.get('last_name', '')}\n"
        f"Číslo karty: {data.get('membership_id', '')}\n"
        f"Datum narození: {data.get('dob', '')}\n"
        f"Email: {data.get('email', '')}\n"
        f"Telefon: {data.get('phone', '')}"
    )
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#ffffff", back_color="#36378c")
    img.save(output_path)
    return output_path

def generate_qr_code_bytes(data: Dict[str, str]):
    """
    Generates a QR code image from the application data and returns it as bytes.
    Payload format: First|Last|DOB|Email|MembershipID
    """
    from io import BytesIO
    
    # Construct payload
    payload = (
        f"Jméno: {data.get('first_name') or ''}\n"
        f"Příjmení: {data.get('last_name') or ''}\n"
        f"Číslo karty: {data.get('membership_id') or ''}\n"
        f"Datum narození: {data.get('dob') or ''}\n"
        f"Email: {data.get('email') or ''}\n"
        f"Telefon: {data.get('phone') or ''}"
    )
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#ffffff", back_color="#36378c")
    
    # Save to BytesIO instead of file
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

from datetime import datetime

def calculate_age(dob_str: str) -> int:
    """Calculates age from DOB string. Supports DD/MM/YYYY and DD.MM.YYYY."""
    try:
        # Normalize separators
        clean_dob = dob_str.strip().replace(" ", "").replace(".", "/")
        # Handle cases like 14/5/2000 -> 14/05/2000
        parts = clean_dob.split("/")
        if len(parts) == 3:
            clean_dob = f"{int(parts[0]):02d}/{int(parts[1]):02d}/{parts[2]}"
            
        dob = datetime.strptime(clean_dob, "%d/%m/%Y")
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except ValueError:
        return 0

import unicodedata

def normalize_text(text: str) -> str:
    """Removes accents and converts to lowercase."""
    if not text:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()



def generate_membership_card(data: Dict[str, str]):
    """
    Generates a membership card image using the template.
    Returns bytes of the PNG image.
    """
    from io import BytesIO
    import os
    
    # Load the template
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'card_template.jpg')
    card = Image.open(template_path)
    
    
    # Get card dimensions
    width, height = card.size
    
    # Create a drawing context
    draw = ImageDraw.Draw(card)
    
    # 1. Generate QR Code
    qr_img = generate_qr_code_bytes(data)
    qr_pil = Image.open(qr_img)
    
    # Resize QR code - smaller to fit in top left corner
    qr_size = int(height * 0.55)  # 55% of card height
    # Use LANCZOS for better quality downscaling
    qr_pil = qr_pil.resize((qr_size, qr_size), Image.LANCZOS)
    
    # Position QR code in TOP LEFT corner (not covering faces)
    qr_x = 50
    qr_y = 22  # Top position
    card.paste(qr_pil, (qr_x, qr_y))
    
    # 2. Load fonts
    try:
        # Noto Sans Mono Bold from project fonts directory
        # Use absolute path to ensure it loads correctly
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_path = os.path.join(base_dir, 'fonts', 'NotoSansMono-Bold.ttf')
        
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Font not found at {font_path}")
            
        font_number = ImageFont.truetype(font_path, 28)
        font_name = ImageFont.truetype(font_path, 28)
    except Exception as e:
        print(f"Warning: Could not load Noto Sans Mono Bold: {e}")
        try:
            # Fallback to Courier New Bold
            font_number = ImageFont.truetype("/System/Library/Fonts/Supplemental/Courier New Bold.ttf", 28)
            font_name = ImageFont.truetype("/System/Library/Fonts/Supplemental/Courier New Bold.ttf", 28)
        except:
            font_number = ImageFont.load_default()
            font_name = ImageFont.load_default()
    
    # 3. Draw membership number (to the right of QR code, top aligned)
    membership_id = data.get('membership_id') or '0000'
    membership_id = str(membership_id) # Ensure string
    # Position to the right of QR code
    number_x = qr_x + qr_size + 30  # 30px gap from QR code
    number_y = qr_y + 45  # Moved another 10px lower
    
    draw.text((number_x, number_y), membership_id, font=font_number, fill="white")
    
    # 4. Draw full name (below membership number, same x position)
    first_name = data.get('first_name') or ''
    last_name = data.get('last_name') or ''
    full_name = f"{first_name} {last_name}".strip()
    
    name_x = number_x
    name_y = number_y + 90  # Below the number
    
    draw.text((name_x, name_y), full_name, font=font_name, fill="white")
    
    # Save to bytes
    img_io = BytesIO()
    card.save(img_io, 'PNG', optimize=True)
    img_io.seek(0)
    return img_io

if __name__ == "__main__":
    # Test run
    test_data = {
        'first_name': 'Barbora',
        'last_name': 'Smékalová',
        'email': 'barus.smekalova@outlook.cz',
        'dob': '14/05/2000',
        'membership_id': '1954',
        'full_body': 'Full text content here...'
    }
    
    # Create a temp dir for artifacts if needed, or just use current
    qr_path = "test_qr.png"
    doc_path = "test_application.docx"
    
    generate_qr_code(test_data, qr_path)
    # generate_document(test_data, qr_path, doc_path)
    
    # Cleanup
    if os.path.exists(qr_path):
        os.remove(qr_path)

# Alias for compatibility
generate_card = generate_membership_card
