import requests
from datetime import datetime

def send_message(message):
    message_id = generate_message_id()
    payload = {
        'message_id': message_id,
        'message': message
    }
    response = requests.post('http://localhost:3000/webhook', json=payload)
    if response.status_code == 200:
        print('Message sent successfully')
    else:
        print('Failed to send message')

def generate_message_id():
    now = datetime.now()
    timestamp = now.timestamp()
    return f'msg_{int(timestamp)}'

if __name__ == '__main__':
    send_message('hello world')
