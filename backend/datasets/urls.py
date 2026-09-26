from django.urls import path
from . import views

urlpatterns = [
    path(
        'datasets/',
        views.DatasetListCreateView.as_view(),
        name='dataset-list-create'
    ),
    # Upload endpoint — must come BEFORE datasets/<int:pk>/ so Django
    # doesn't try to match the word "upload" as a primary key integer.
    path(
        'datasets/upload/',
        views.CSVUploadView.as_view(),
        name='dataset-upload'
    ),
    path(
        'datasets/<int:pk>/',
        views.DatasetDetailView.as_view(),
        name='dataset-detail'
    ),
]