# core/utils.py
import binascii
import os
from django.utils import timezone
from datetime import timedelta

def generate_activation_token():
    return binascii.hexlify(os.urandom(20)).decode()

def create_activation_link(user):
    token = binascii.hexlify(os.urandom(20)).decode()

    profile = user.profile
    profile.activation_token = token
    profile.activation_expiry = timezone.now() + timedelta(hours=24)
    profile.save()

    return f"http://127.0.0.1:8000/activate/{token}/"
