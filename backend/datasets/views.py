from rest_framework import generics
from .models import Dataset
from .serializers import DatasetSerializer


class DatasetListCreateView(generics.ListCreateAPIView):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
