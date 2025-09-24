<<<<<<< HEAD
from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    username = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)    
    
    def __str__(self):
=======
from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    username = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)    
    
    def __str__(self):
>>>>>>> origin/feature/SCRUM-125-Implementar-identificador-de-ofertas-por-categoría
        return self.username