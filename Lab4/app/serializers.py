from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers

from .models import *


class CategorysSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)
    image = serializers.ImageField(required=True)
    sex = serializers.CharField(required=True)

    class Meta:
        model = Category
        fields = ("id", "name", "status", "sex", "age", "image")


class CategorySerializer(CategorysSerializer):
    class Meta(CategorysSerializer.Meta):
        fields = "__all__"


class CategoryAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("name", "description", "sex", "image")


class ImtBaseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)
    owner = serializers.StringRelatedField(read_only=True)
    moderator = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Imt
        fields = "__all__"


class ImtsSerializer(ImtBaseSerializer):
    categorys_count = serializers.SerializerMethodField()
    categorys_calculated = serializers.SerializerMethodField()

    @swagger_serializer_method(serializer_or_field=serializers.IntegerField())
    def get_categorys_count(self, imt):
        items = CategoryImt.objects.filter(imt=imt)
        return items.count()

    @swagger_serializer_method(serializer_or_field=serializers.IntegerField())
    def get_categorys_calculated(self, imt):
        items = CategoryImt.objects.filter(imt=imt)
        return items.filter(factor__gte=0).count()

class CategoryItemSerializer(CategorySerializer):
    weight = serializers.SerializerMethodField()

    @swagger_serializer_method(serializer_or_field=serializers.IntegerField(required=True))
    def get_weight(self, _):
        return self.context.get("weight", 0)

    class Meta:
        model = Category
        fields = ("id", "name", "status", "sex", "image", "weight")


class CategoryItemSerializerWithCalc(CategoryItemSerializer):
    factor = serializers.SerializerMethodField()

    def get_factor(self, _):
        return self.context.get("factor")

    class Meta:
        model = Category
        fields = ("id", "name", "status", "sex", "image", "weight", "factor")


class CategoryImtSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryImt
        fields = "__all__"


class ImtSerializer(ImtBaseSerializer):
    categorys = serializers.SerializerMethodField()

    @swagger_serializer_method(serializer_or_field=CategoryItemSerializerWithCalc(many=True))
    def get_categorys(self, imt):
        items = CategoryImt.objects.filter(imt=imt)

        if imt.status == 3:
            return [CategoryItemSerializerWithCalc(item.category, context={"weight": item.weight, "height": item.height,
                                                                         "factor": item.factor}).data for
                    item in items]

        return [CategoryItemSerializer(item.category, context={"weight": item.weight, "height": item.height}).data for item in items]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', "is_superuser")


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'username')
        write_only_fields = ('password',)
        read_only_fields = ('id',)

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['username']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class UserUpdateProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    username = serializers.CharField(write_only=True, required=False, allow_blank=True)
    email = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        instance = super().update(instance, validated_data)

        if password and password.strip() and not self.instance.check_password(password):
            instance.set_password(password)
            instance.save()

        return instance
