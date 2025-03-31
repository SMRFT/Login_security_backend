from django.db import models

# Create your models here.

from django.db import models
from django.utils.timezone import now
import pytz

IST = pytz.timezone('Asia/Kolkata')

class User(models.Model):
    employeeId = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)  # Sets is_active to True by default
    created_date = models.DateTimeField(default=lambda: now().astimezone(IST))  # Indian Timezone
    created_by = models.CharField(max_length=100, default='system')  # Default 'system'
    lastmodified_by = models.CharField(max_length=100, default='system')  # Default 'system'
    lastmodified_date = models.DateTimeField(default=lambda: now().astimezone(IST))  # Indian Timezone

    def __str__(self):
        return self.employeeId