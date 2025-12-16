from PIL import Image, ImageDraw, ImageFont
import qrcode
from io import BytesIO

# Sample data
test_data = {
    'first_name': 'Marie',
    'last_name': 'Dinkovová',
    'membership_id': '0923',
    'dob': '01.01.2000',
    'email': 'marie@example.com',
    'phone': '123456789'
}

# Load the blank card template
template_path = '/Users/tomas.dinkov/.gemini/antigravity/brain/4a8cd8f2-e24e-4009-90af-14b5a24f6d66/uploaded_image_1764086221517.jpg'
card = Image.open(template_path)

# Get card dimensions
width, height = card.size
print(f"Card dimensions: {width}x{height}")

# Create a drawing context
draw = ImageDraw.Draw(card)

# 1. Generate QR Code
payload = (
    f"Jméno: {test_data.get('first_name', '')}\\n"
    f"Příjmení: {test_data.get('last_name', '')}\\n"
    f"Číslo karty: {test_data.get('membership_id', '')}\\n"
    f"Datum narození: {test_data.get('dob', '')}\\n"
    f"Email: {test_data.get('email', '')}\\n"
    f"Telefon: {test_data.get('phone', '')}"
)

qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=2,
)
qr.add_data(payload)
qr.make(fit=True)

qr_img = qr.make_image(fill_color="white", back_color="#36378c")

# Resize QR code - smaller to fit in top left corner
qr_size = int(height * 0.55)  # 55% of card height
qr_img = qr_img.resize((qr_size, qr_size))

# Position QR code in TOP LEFT corner (not covering faces)
qr_x = 50
qr_y = 50  # Top position
card.paste(qr_img, (qr_x, qr_y))

# 2. Load fonts (try different sizes)
try:
    font_number = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 70)
    font_name = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 45)
except:
    try:
        font_number = ImageFont.truetype("Arial.ttf", 70)
        font_name = ImageFont.truetype("Arial.ttf", 45)
    except:
        font_number = ImageFont.load_default()
        font_name = ImageFont.load_default()

# 3. Draw membership number (to the right of QR code, top aligned)
membership_id = test_data.get('membership_id', '0000')
# Position to the right of QR code
number_x = qr_x + qr_size + 30  # 30px gap from QR code
number_y = qr_y + 20  # Aligned with top of QR

draw.text((number_x, number_y), membership_id, font=font_number, fill="white")

# 4. Draw full name (below membership number, same x position)
full_name = f"{test_data.get('first_name', '')} {test_data.get('last_name', '')}"
name_x = number_x
name_y = number_y + 90  # Below the number

draw.text((name_x, name_y), full_name, font=font_name, fill="white")

# Save the example
output_path = '/Users/tomas.dinkov/Desktop/md_application_processor/example_card.png'
card.save(output_path)
print(f"Example card saved to: {output_path}")
