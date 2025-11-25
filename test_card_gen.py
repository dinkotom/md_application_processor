from src.generator import generate_membership_card
import os

test_data = {
    'first_name': 'Jan',
    'last_name': 'Novák',
    'membership_id': '1234',
    'dob': '01.01.2000',
    'email': 'jan@example.com',
    'phone': '123456789'
}

try:
    print("Generating card...")
    img_io = generate_membership_card(test_data)
    
    with open('test_card_output.png', 'wb') as f:
        f.write(img_io.getvalue())
        
    print(f"Card saved to test_card_output.png. Size: {os.path.getsize('test_card_output.png')} bytes")
except Exception as e:
    print(f"Error: {e}")
