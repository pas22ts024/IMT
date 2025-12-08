import uuid
from datetime import timedelta

from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .calc import calc
from .permissions import IsModerator, IsAuthenticated, IsBuyer
from .redis import session_storage
from .serializers import *
from .utils import get_session, get_draft_imt, identity_user


@swagger_auto_schema(
    method='GET',
    manual_parameters=[
        openapi.Parameter(
            'category_name',
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING
        )
    ],
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=CategorysSerializer(many=True),
            description=""
        )
    }
)
@api_view(["GET"])
def search_categorys(request):
    category_name = request.GET.get("category_name", "")

    categorys = Category.objects.filter(status=1)
    if category_name:
        categorys = categorys.filter(name__icontains=category_name)

    serializer = CategorysSerializer(categorys, many=True)

    return Response(serializer.data)


@swagger_auto_schema(
    method='GET',
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=CategorySerializer,
            description=""
        )
    }
)
@api_view(["GET"])
def get_category_by_id(request, category_id):
    if not Category.objects.filter(pk=category_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    category = Category.objects.get(pk=category_id)
    serializer = CategorySerializer(category)

    return Response(serializer.data)


@swagger_auto_schema(
    method='PUT',
    request_body=CategorySerializer,
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=CategorySerializer,
            description=""
        )
    }
)
@api_view(["PUT"])
@permission_classes([IsModerator])
def update_category(request, category_id):
    if not Category.objects.filter(pk=category_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    category = Category.objects.get(pk=category_id)

    serializer = CategorySerializer(category, data=request.data, partial=True)

    if serializer.is_valid(raise_exception=True):
        serializer.save()

    return Response(serializer.data)


@swagger_auto_schema(
    method='POST',
    request_body=CategoryAddSerializer,
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=CategorySerializer,
            description=""
        )
    }
)
@api_view(["POST"])
@permission_classes([IsModerator])
def create_category(request):
    serializer = CategoryAddSerializer(data=request.data, partial=False)

    serializer.is_valid(raise_exception=True)

    Category.objects.create(**serializer.validated_data)

    categorys = Category.objects.filter(status=1)
    serializer = CategorySerializer(categorys, many=True)

    return Response(serializer.data)


@swagger_auto_schema(
    method='DELETE',
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=CategorySerializer,
            description=""
        )
    }
)
@api_view(["DELETE"])
@permission_classes([IsModerator])
def delete_category(request, category_id):
    if not Category.objects.filter(pk=category_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    category = Category.objects.get(pk=category_id)
    category.status = 2
    category.save()

    categorys = Category.objects.filter(status=1)
    serializer = CategorySerializer(categorys, many=True)

    return Response(serializer.data)


@swagger_auto_schema(
    method='POST',
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=ImtSerializer,
            description=""
        )
    }
)
@api_view(["POST"])
@permission_classes([IsBuyer])
def add_category_to_imt(request, category_id):
    if not Category.objects.filter(pk=category_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    category = Category.objects.get(pk=category_id)

    draft_imt = get_draft_imt(request)

    if draft_imt is None:
        draft_imt = Imt.objects.create()
        draft_imt.owner = identity_user(request)
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


@swagger_auto_schema(
    method='POST',
    manual_parameters=[
        openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE),
    ],
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=CategorySerializer,
            description=""
        )
    }
)
@api_view(["POST"])
@permission_classes([IsModerator])
@parser_classes((MultiPartParser,))
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


@swagger_auto_schema(
    method='GET',
    manual_parameters=[
        openapi.Parameter(
            'status',
            openapi.IN_QUERY,
            type=openapi.TYPE_NUMBER
        ),
        openapi.Parameter(
            'date_formation_start',
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'date_formation_end',
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING
        )
    ],
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=ImtsSerializer(many=True),
            description=""
        )
    }
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_imts(request):
    status = int(request.GET.get("status", 0))
    date_formation_start = request.GET.get("date_formation_start")
    date_formation_end = request.GET.get("date_formation_end")

    imts = Imt.objects.exclude(status__in=[1, 5])

    user = identity_user(request)
    if not user.is_superuser:
        imts = imts.filter(owner=user)

    if status > 0:
        imts = imts.filter(status=status)

    if date_formation_start and parse_datetime(date_formation_start):
        imts = imts.filter(date_formation__gt=parse_datetime(date_formation_start) - timedelta(days=1))

    if date_formation_end and parse_datetime(date_formation_end):
        imts = imts.filter(date_formation__lt=parse_datetime(date_formation_end) + timedelta(days=1))

    serializer = ImtsSerializer(imts, many=True)

    return Response(serializer.data)


@swagger_auto_schema(
    method='GET',
    responses={
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "categorys_count": openapi.Schema(type=openapi.TYPE_NUMBER),
                "draft_imt": openapi.Schema(type=openapi.TYPE_NUMBER)
            },
            required=["categorys_count", "draft_imt"]
        )
    }
)
@api_view(["GET"])
@permission_classes([IsBuyer])
def get_cart_info(request):
    resp = {
        "categorys_count": 0,
        "draft_imt": 0
    }

    draft_imt = get_draft_imt(request)
    if draft_imt:
        categorys = CategoryImt.objects.filter(imt=draft_imt)
        resp = {
            "categorys_count": categorys.count(),
            "draft_imt": draft_imt.pk
        }

    return Response(resp)


@swagger_auto_schema(
    method='GET',
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=ImtSerializer,
            description=""
        )
    }
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_imt_by_id(request, imt_id):
    if not Imt.objects.filter(pk=imt_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    imt = Imt.objects.get(pk=imt_id)

    user = identity_user(request)
    if not user.is_superuser and imt.owner != user:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = ImtSerializer(imt, many=False)
    return Response(serializer.data)


@swagger_auto_schema(
    method='PUT',
    request_body=ImtSerializer,
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=ImtSerializer,
            description=""
        )
    }
)
@api_view(["PUT"])
@permission_classes([IsBuyer])
def update_imt(request, imt_id):
    user = identity_user(request)
    if not Imt.objects.filter(pk=imt_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    imt = Imt.objects.get(pk=imt_id)
    serializer = ImtSerializer(imt, data=request.data, partial=True)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    return Response(serializer.data)


@swagger_auto_schema(
    method='PUT',
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=ImtSerializer,
            description=""
        )
    }
)
@api_view(["PUT"])
@permission_classes([IsBuyer])
def update_status_user(request, imt_id):
    user = identity_user(request)
    if not Imt.objects.filter(pk=imt_id, owner=user).exists():
        return Response({
            "error": "заключение не найден"
        }, status=status.HTTP_404_NOT_FOUND)

    imt = Imt.objects.get(pk=imt_id)

    if imt.status != 1:
        return Response({
            "error": "заключение не в том статусе"
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    imt.status = 2
    imt.date_formation = timezone.now()
    imt.save()

    serializer = ImtSerializer(imt)
    return Response(serializer.data)


@swagger_auto_schema(
    method='PUT',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'status': openapi.Schema(type=openapi.TYPE_NUMBER),
        }
    ),
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=ImtSerializer,
            description=""
        )
    }
)
@api_view(["PUT"])
@permission_classes([IsModerator])
def update_status_admin(request, imt_id):
    if not Imt.objects.filter(pk=imt_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

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
    imt.moderator = identity_user(request)
    imt.save()

    serializer = ImtSerializer(imt)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='DELETE',
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=ImtSerializer,
            description=""
        )
    }
)
@api_view(["DELETE"])
@permission_classes([IsBuyer])
def delete_imt(request, imt_id):
    user = identity_user(request)
    if not Imt.objects.filter(pk=imt_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    imt = Imt.objects.get(pk=imt_id)

    if imt.status != 1:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    imt.status = 5
    imt.save()

    serializer = ImtSerializer(imt, many=False)

    return Response(serializer.data)


@swagger_auto_schema(
    method='DELETE',
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=CategoryItemSerializer(many=True),
            description=""
        )
    }
)
@api_view(["DELETE"])
@permission_classes([IsBuyer])
def delete_category_from_imt(request, imt_id, category_id):
    user = identity_user(request)
    if not Imt.objects.filter(pk=imt_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not CategoryImt.objects.filter(imt_id=imt_id, category_id=category_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    item = CategoryImt.objects.get(imt_id=imt_id, category_id=category_id)
    item.delete()

    items = CategoryImt.objects.filter(imt_id=imt_id)
    data = [CategoryItemSerializer(item.category, context={"weight": item.weight}).data for item in items]

    return Response(data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='PUT',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'weight': openapi.Schema(type=openapi.TYPE_NUMBER),
        },
        required=["weight"],
    ),
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=CategoryImtSerializer,
            description=""
        )
    }
)
@api_view(["PUT"])
@permission_classes([IsBuyer])
def update_category_in_imt(request, imt_id, category_id):
    user = identity_user(request)
    if not Imt.objects.filter(pk=imt_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

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


@swagger_auto_schema(
    method='POST',
    request_body=UserRegisterSerializer,
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=UserSerializer,
            description=""
        )
    }
)
@api_view(["POST"])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    user = serializer.save()

    session_id = str(uuid.uuid4())
    session_storage.set(session_id, user.id)

    serializer = UserSerializer(user)
    response = Response(serializer.data, status=status.HTTP_201_CREATED)
    response.set_cookie("session_id", session_id, samesite="lax")

    return response


@swagger_auto_schema(
    method='POST',
    request_body=UserLoginSerializer,
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=UserSerializer,
            description=""
        )
    }
)
@api_view(["POST"])
def login(request):
    serializer = UserLoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(**serializer.data)
    if user is None:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    session_id = str(uuid.uuid4())
    session_storage.set(session_id, user.id)

    serializer = UserSerializer(user)
    response = Response(serializer.data, status=status.HTTP_200_OK)
    response.set_cookie("session_id", session_id, samesite="lax")

    return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    session = get_session(request)
    session_storage.delete(session)

    response = Response(status=status.HTTP_200_OK)
    response.delete_cookie('session_id')

    return response


@swagger_auto_schema(
    method='GET',
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=UserSerializer,
            description=""
        )
    }
)
@api_view(["GET"])
def user_info(request):
    user = identity_user(request)
    if user is None:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    serializer = UserSerializer(user, many=False)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='PUT',
    request_body=UserUpdateProfileSerializer,
    responses={
        status.HTTP_200_OK: openapi.Response(
            schema=UserUpdateProfileSerializer,
            description=""
        )
    }
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user(request):
    user = identity_user(request)

    serializer = UserUpdateProfileSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data)
