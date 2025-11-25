from django.urls import path
from .views import *

urlpatterns = [
    path('', index),
    path('categorys/<int:category_id>/', category_page, name="category_page"),
    path('imts/<int:imt_id>/', imt_page, name="imt_page"),
    path('categorys/<int:category_id>/add_to_imt/', add_category_to_draft_imt, name="add_category_to_draft_imt"),
    path('imts/<int:imt_id>/delete/', delete_imt, name="delete_imt")
]
