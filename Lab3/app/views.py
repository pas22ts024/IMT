from datetime import timedelta

from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .calc import calc
from .serializers import *


def get_draft_imt():
    return Imt.objects.filter(status=1).first()


def get_user():
    return User.objects.filter(is_superuser=False).first()


def get_moderator():
    return User.objects.filter(is_superuser=True).first()


def identity_user(request):
    return get_user()


@api_view(["GET"])
def search_categorys(request):
    category_name = request.GET.get("category_name", "")

    categorys = Category.objects.filter(status=1)

    if category_name:
        categorys = categorys.filter(name__icontains=category_name)

    serializer = CategorysSerializer(categorys, many=True)

    return Response(serializer.data)


@api_view(["GET"])
def get_category_by_id(request, category_id):
    if not Category.objects.filter(pk=category_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    category = Category.objects.get(pk=category_id)
    serializer = CategorySerializer(category)

    return Response(serializer.data)


@api_view(["PUT"])
def update_category(request, category_id):
    if not Category.objects.filter(pk=category_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    category = Category.objects.get(pk=category_id)

    serializer = CategorySerializer(category, data=request.data, partial=True)

    if serializer.is_valid(raise_exception=True):
        serializer.save()

    return Response(serializer.data)


@api_view(["POST"])
def create_category(request):
    serializer = CategorySerializer(data=request.data, partial=False)

    serializer.is_valid(raise_exception=True)

    Category.objects.create(**serializer.validated_data)

    categorys = Category.objects.filter(status=1)
    serializer = CategorySerializer(categorys, many=True)

    return Response(serializer.data)


@api_view(["DELETE"])
def delete_category(request, category_id):
    if not Category.objects.filter(pk=category_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    category = Category.objects.get(pk=category_id)
    category.status = 2
    category.save()

    categorys = Category.objects.filter(status=1)
    serializer = CategorySerializer(categorys, many=True)

    return Response(serializer.data)


@api_view(["POST"])
def add_category_to_imt(request, category_id):
    if not Category.objects.filter(pk=category_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    category = Category.objects.get(pk=category_id)

    draft_imt = get_draft_imt()

    if draft_imt is None:
        draft_imt = Imt.objects.create()
        draft_imt.owner = get_user()
        draft_imt.save()

    if CategoryImt.objects.filter(imt=draft_imt, category=category).exists():
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    item = CategoryImt.objects.create(
        imt=draft_imt,
        category=category
    )
    item.save()

    serializer = ImtSerializer(draft_imt)
    return Response(serializer.data["categorys"])


@api_view(["POST"])
def update_category_image(request, category_id):
    if not Category.objects.filter(pk=category_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    category = Category.objects.get(pk=category_id)

    image = request.data.get("image")
    if image is None:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    category.image = image
    category.save()

    serializer = CategorySerializer(category)
    return Response(serializer.data)


@api_view(["GET"])
def search_imts(request):
    status = int(request.GET.get("status", 0))
    date_formation_start = request.GET.get("date_formation_start")
    date_formation_end = request.GET.get("date_formation_end")

    imts = Imt.objects.exclude(status__in=[1, 5])

    if status > 0:
        imts = imts.filter(status=status)

    if date_formation_start and parse_datetime(date_formation_start):
        imts = imts.filter(date_formation__gt=parse_datetime(date_formation_start) - timedelta(days=1))

    if date_formation_end and parse_datetime(date_formation_end):
        imts = imts.filter(date_formation__lt=parse_datetime(date_formation_end) + timedelta(days=1))

    serializer = ImtsSerializer(imts, many=True)

    return Response(serializer.data)


@api_view(["GET"])
def get_cart_info(request):
    resp = {
        "categorys_count": 0,
        "draft_imt": 0
    }

    draft_imt = get_draft_imt()
    if draft_imt:
        categorys = CategoryImt.objects.filter(imt=draft_imt)
        resp = {
            "categorys_count": categorys.count(),
            "draft_imt": draft_imt.pk
        }

    return Response(resp)


@api_view(["GET"])
def get_imt_by_id(request, imt_id):
    if not Imt.objects.filter(pk=imt_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    imt = Imt.objects.get(pk=imt_id)
    serializer = ImtSerializer(imt, many=False)

    return Response(serializer.data)


@api_view(["PUT"])
def update_imt(request, imt_id):
    if not Imt.objects.filter(pk=imt_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    imt = Imt.objects.get(pk=imt_id)
    serializer = ImtSerializer(imt, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


@api_view(["PUT"])
def update_status_user(request, imt_id):
    if not Imt.objects.filter(pk=imt_id).exists():
        return Response({
                "error": "заключение не найден"
        }, status=status.HTTP_404_NOT_FOUND)

    imt = Imt.objects.get(pk=imt_id)

    if imt.status != 1:
        return Response({
                "error": "заключение не в том статусе"
        },status=status.HTTP_405_METHOD_NOT_ALLOWED)

    if not imt.related:
        return Response({
            "error": "поле related не заполнено"
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    imt.status = 2
    imt.date_formation = timezone.now()
    imt.save()

    serializer = ImtSerializer(imt)

    return Response(serializer.data)


@api_view(["PUT"])
def update_status_admin(request, imt_id):
    if not Imt.objects.filter(pk=imt_id).exists():
        return Response({
                "error": "заключение не найден"
            }, status=status.HTTP_404_NOT_FOUND)

    request_status = int(request.data["status"])
    if request_status not in [3, 4]:
        return Response({
                "error": "некорректный status"
            }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    imt = Imt.objects.get(pk=imt_id)

    if imt.status != 2:
        return Response({
                "error": "заключение не в том статусе"
            }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    if request_status == 3:
        for item in CategoryImt.objects.filter(imt=imt):
            item.factor = calc(imt, item)
            item.save()

    imt.date_complete = timezone.now()
    imt.status = request_status
    imt.moderator = get_moderator()
    imt.save()

    serializer = ImtSerializer(imt)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["DELETE"])
def delete_imt(request, imt_id):
    if not Imt.objects.filter(pk=imt_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    imt = Imt.objects.get(pk=imt_id)

    if imt.status != 1:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    imt.status = 5
    imt.save()

    serializer = ImtSerializer(imt, many=False)

    return Response(serializer.data)


@api_view(["DELETE"])
def delete_category_from_imt(request, imt_id, category_id):
    if not CategoryImt.objects.filter(imt_id=imt_id, category_id=category_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    item = CategoryImt.objects.get(imt_id=imt_id, category_id=category_id)
    item.delete()

    items = CategoryImt.objects.filter(imt_id=imt_id)
    data = [CategoryItemSerializer(item.category, context={"weight": item.weight, "height": item.height}).data for item in items]

    return Response(data, status=status.HTTP_200_OK)


@api_view(["PUT"])
def update_category_in_imt(request, imt_id, category_id):
    if not CategoryImt.objects.filter(category_id=category_id, imt_id=imt_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    imt = Imt.objects.get(pk=imt_id)
    if imt.status != 1:
        return Response({
            "error": "Некорректный статус заключения"
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    item = CategoryImt.objects.get(category_id=category_id, imt_id=imt_id)

    serializer = CategoryImtSerializer(item, data=request.data, partial=True)

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data)


@api_view(["POST"])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    user = serializer.save()

    serializer = UserSerializer(user)

    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def login(request):
    serializer = UserLoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(**serializer.data)
    if user is None:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    serializer = UserSerializer(user)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def logout(request):
    return Response(status=status.HTTP_200_OK)


@api_view(["GET"])
def user_info(request):
    user = identity_user(request)
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT"])
def update_user(request):
    user = identity_user(request)

    serializer = UserUpdateProfileSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data)