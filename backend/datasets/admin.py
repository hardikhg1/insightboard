from django.contrib import admin
from .models import Dataset, DatasetColumn, DataRow

admin.site.register(Dataset)
admin.site.register(DatasetColumn)
admin.site.register(DataRow)
# Register your models here.
