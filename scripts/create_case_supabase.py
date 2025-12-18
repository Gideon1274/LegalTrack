import os
import sys
import pathlib
import django

# Ensure project root is on sys.path so Django can import the project package
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legaltrack.settings')
# Ensure .env is loaded by settings when we import Django
django.setup()

from core.models import CustomUser, Case

u = CustomUser.objects.filter(is_superuser=True).first()
if not u:
    print('No superuser found: creating one (super@local)')
    u = CustomUser.objects.create_superuser(email='super@local', password='testpass123')
else:
    print('Using existing superuser:', u.email)

c = Case.objects.create(client_name='Test Client from agent', client_contact='test@local', submitted_by=u, checklist=[])
print('Created Case:', c.tracking_id, c.id)
print('Total Cases:', Case.objects.count())
