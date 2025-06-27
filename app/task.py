from celery import Celery
from datetime import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import os


celery = Celery('tasks', broker='redis://localhost:6379/0')
def newvalidate_and_format_phone_number(phone_number):
    # Assuming phone_number is a string
    # Validate and format the phone number if necessary
    # Add the country code if missing

    # Example: Assuming Indian country code is +91
    phone_number=str(phone_number)
    if not phone_number.startswith('+'):
        phone_number = '+91' + phone_number

    return phone_number

@celery.task
def send_alter(numbers_to_message, message_body):
    print("Sending SMS for late out time at", datetime.now())
