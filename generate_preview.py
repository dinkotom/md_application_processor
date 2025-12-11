import os
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('welcome_email.html')
output = template.render()
with open('preview.html', 'w') as f:
    f.write(output)
print("Preview generated.")
