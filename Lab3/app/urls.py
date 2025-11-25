from django.urls import path
from .views import *

urlpatterns = [
    path('api/categorys/', search_categorys),  # GET
    path('api/categorys/<int:category_id>/', get_category_by_id),  # GET
    path('api/categorys/<int:category_id>/update/', update_category),  # PUT
    path('api/categorys/<int:category_id>/update_image/', update_category_image),  # POST
    path('api/categorys/<int:category_id>/delete/', delete_category),  # DELETE
    path('api/categorys/create/', create_category),  # POST
    path('api/categorys/<int:category_id>/add_to_imt/', add_category_to_imt),  # POST

    path('api/imts/', search_imts),  # GET
    path('api/imts/cart/', get_cart_info),  # GET
    path('api/imts/<int:imt_id>/', get_imt_by_id),  # GET
    path('api/imts/<int:imt_id>/update/', update_imt),  # PUT
    path('api/imts/<int:imt_id>/update_status_user/', update_status_user),  # PUT
    path('api/imts/<int:imt_id>/update_status_admin/', update_status_admin),  # PUT
    path('api/imts/<int:imt_id>/delete/', delete_imt),  # DELETE

    path('api/imts/<int:imt_id>/update_category/<int:category_id>/', update_category_in_imt),  # PUT
    path('api/imts/<int:imt_id>/delete_category/<int:category_id>/', delete_category_from_imt),  # DELETE

    path('api/users/register/', register), # POST
    path('api/users/update/', update_user), # PUT
    path("api/users/info/", user_info), # GET
    path('api/users/login/', login), # POST
    path('api/users/logout/', logout), # POST
]
