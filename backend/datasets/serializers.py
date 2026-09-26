from rest_framework import serializers
from .models import Dataset


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = [
            'id',
            'name',
            'original_filename',
            'uploaded_at',
            'row_count',
            'column_count'
        ]