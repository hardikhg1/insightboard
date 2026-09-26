from rest_framework import serializers

from .models import DataRow, Dataset, DatasetColumn


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


class DatasetColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetColumn
        fields = [
            'id',
            'name',
            'position',
            'data_type'
        ]


class DataRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataRow
        fields = [
            'id',
            'row_index',
            'data'
        ]
class DatasetDetailSerializer(serializers.ModelSerializer):
    columns = DatasetColumnSerializer(many=True, read_only=True)
    rows = DataRowSerializer(many=True, read_only=True)

    class Meta:
        model = Dataset
        fields = [
            'id',
            'name',
            'original_filename',
            'uploaded_at',
            'row_count',
            'column_count',
            'columns',
            'rows'
        ]
