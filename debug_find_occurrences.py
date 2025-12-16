
import os

filepath = 'samples/extracted_email.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = "Vítej v klubu"
start = 0
while True:
    idx = content.find(target, start)
    if idx == -1:
        break
    
    print(f"Found at index {idx}")
    # Print surrounding context
    ctx_start = max(0, idx - 100)
    ctx_end = min(len(content), idx + 200)
    print(f"Context: {content[ctx_start:ctx_end]}")
    print("-" * 40)
    
    start = idx + 1
