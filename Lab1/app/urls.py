from django.urls import path
from .views import *

urlpatterns = [
    path('', index),
    path('categorys/<int:category_id>/', category_page),
    path('imts/<int:imt_id>/', imt_page),
]