<<<<<<< HEAD
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')
        
        def create(self, validated_data):
                   # Crea usuario y encripta password
            user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
=======
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')
        
        def create(self, validated_data):
                   # Crea usuario y encripta password
            user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
>>>>>>> origin/feature/SCRUM-125-Implementar-identificador-de-ofertas-por-categoría
            return user