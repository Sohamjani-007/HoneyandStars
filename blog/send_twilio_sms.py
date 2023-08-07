from twilio.rest import Client
from django.conf import settings

account_sid = 'ACa2d60cd5f68c50b32c81a6682f869eb9'
auth_token = '7db184cd0828550988dc837eb5580962'

client = Client(account_sid, auth_token)
client.messages.create(from_='+15074146977',
                       to='+917977292053',
                       body='Hey Soham, You are Genius.Billionaire.Philanthropist.')

def send_sms(to, body):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        to=to,
        from_=settings.TWILIO_PHONE_NUMBER,
        body=body
    )
    return message.sid

