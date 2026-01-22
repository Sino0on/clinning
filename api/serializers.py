from rest_framework import serializers
from .models import *


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        # Важно: поля key и value должны быть здесь, чтобы они попали в data
        fields = ['key', 'value', 'value_ru', 'created_at', 'updated_at']

    def to_representation(self, instance):
        # 1. Получаем стандартный словарь данных (где key и value — отдельные поля)
        representation = super().to_representation(instance)

        # 2. Извлекаем (вырезаем) key и value из словаря
        # Используем pop, чтобы удалить их из старого места
        key_name = representation.pop('key')
        main_value = representation.pop('value')

        # 3. Формируем новый словарь. 
        # Сначала кладем динамический ключ, потом распаковываем остальные поля (value_ru, dates)
        new_representation = {
            key_name: main_value,  # Вот здесь происходит магия: "test_key": "test_value"
            **representation       # Добавляем value_ru, created_at и т.д.
        }

        return new_representation


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.endswith('.xlsx'):
            raise serializers.ValidationError("Файл должен быть формата .xlsx")
        return value



class PartnersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partners
        fields = '__all__'



class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'


class UseproductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Useproduct
        fields = '__all__'



class BackgroundImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackgroundImage
        fields = '__all__'


class DoiposleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doiposle
        fields = '__all__'
    

