import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from authentication.views import login_view
from django.test import RequestFactory
import json

factory = RequestFactory()
request = factory.post('/api/login/', json.dumps({"employeeId": "test", "password": "password"}), content_type='application/json')
response = login_view(request)
print(response.content)
