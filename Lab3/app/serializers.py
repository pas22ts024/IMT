from rest_framework import serializers

from .models import *


class CategorysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "status", "sex", "age", "image")


class CategorySerializer(CategorysSerializer):
    class Meta(CategorysSerializer.Meta):
        fields = "__all__"


class ImtsSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    moderator = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Imt
        fields = "__all__"


class ImtSerializer(ImtsSerializer):
    categorys = serializers.SerializerMethodField()
            
    def get_categorys(self, imt):
        items = CategoryImt.objects.filter(imt=imt)

        if imt.status == 3:
            return [CategoryItemSerializerWithCalc(item.category, context={"weight": item.weight, "height": item.height, "factor": item.factor}).data for item in items]

        return [CategoryItemSerializer(item.category, context={"weight": item.weight, "height": item.height}).data for item in items]


class CategoryItemSerializer(CategorySerializer):
    weight = serializers.SerializerMethodField()
    height = serializers.SerializerMethodField()

    def get_weight(self, _):
        return self.context.get("weight")

    def get_height(self, _):
        return self.context.get("height")


class CategoryItemSerializerWithCalc(CategoryItemSerializer):
    factor = serializers.SerializerMethodField()

    def get_factor(self, _):
        return self.context.get("factor")


class CategoryImtSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryImt
        fields = "__all__"


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