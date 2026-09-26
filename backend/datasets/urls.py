from django.urls import path
from . import views

urlpatterns = [
    path(
        'datasets/',
        views.DatasetListCreateView.as_view(),
        name='dataset-list-create'
    ),
    path(
        'datasets/<int:pk>/',
        views.DatasetDetailView.as_view(),
        name='dataset-detail'
    ),
]