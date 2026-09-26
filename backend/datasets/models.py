from django.db import models


class Dataset(models.Model):
    name = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    row_count = models.PositiveIntegerField(default=0)
    column_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.name


class DatasetColumn(models.Model):
    TEXT = 'text'
    NUMBER = 'number'
    DATE = 'date'

    TYPE_CHOICES = [
        (TEXT, 'Text'),
        (NUMBER, 'Number'),
        (DATE, 'Date'),
    ]

    dataset = models.ForeignKey(
        Dataset,
        related_name='columns',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    position = models.PositiveIntegerField()
    data_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default=TEXT
    )

    class Meta:
        unique_together = ('dataset', 'name')

    def __str__(self):
        return f"{self.dataset.name} - {self.name}"


class DataRow(models.Model):
    dataset = models.ForeignKey(
        Dataset,
        related_name='rows',
        on_delete=models.CASCADE
    )
    row_index = models.PositiveIntegerField()
    data = models.JSONField()

    class Meta:
        indexes = [
            models.Index(fields=['dataset', 'row_index'])
        ]

    def __str__(self):
        return f"{self.dataset.name} - Row {self.row_index}"