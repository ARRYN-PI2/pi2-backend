import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .serializer import UserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from ...domain.services.mongo_service import guardar_json, obtener_json


class ArchivosJsonView(APIView):
    def post(self, request):
        try:
            raw_body = request.body.decode("utf-8").strip()

            # Si viene como un JSON normal (objeto o lista)
            try:
                data = json.loads(raw_body)
                docs = data if isinstance(data, list) else [data]
            except json.JSONDecodeError:
                # Si falla, asumimos que son múltiples JSONs separados por saltos de línea
                docs = [json.loads(line) for line in raw_body.splitlines() if line.strip()]

            ids = guardar_json("archivos", docs)
            return Response(
                {"mensaje": "Guardado en Mongo", "ids": ids},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request):
        docs = obtener_json("archivos")
        return Response(docs, status=status.HTTP_200_OK)
    
    
@api_view(['GET'])
def getUsers(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(UserSerializer({'username': 'Juan', 'email':'juanmonsalve.23@hotmail.com' }).data)

@api_view(['POST'])
def createUser(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def userDetail(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    