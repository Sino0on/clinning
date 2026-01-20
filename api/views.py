from rest_framework import viewsets
from .models import Item
from .serializers import ItemSerializer


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


import openpyxl
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from .models import Item
from .serializers import FileUploadSerializer

class ItemImportView(APIView):
    parser_classes = [MultiPartParser]  # Важно для приема файлов

    def post(self, request, format=None):
        serializer = FileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']

        try:
            wb = openpyxl.load_workbook(file)
            sheet = wb.active

            # Список для сбора ошибок (если какие-то строки битые)
            errors = []
            
            # Используем атомарную транзакцию: если скрипт упадет, база откатится
            with transaction.atomic():
                # min_row=2 чтобы пропустить заголовок. values_only=True сразу дает значения
                for index, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                    
                    # Проверка на пустую строку (Excel часто грешит "фантомными" строками)
                    if not row or all(cell is None for cell in row):
                        continue
                    
                    # Безопасное извлечение данных (ожидаем 3 колонки)
                    # A -> key, B -> value, C -> value_ru
                    try:
                        key = str(row[0]).strip() if row[0] is not None else None
                        value = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
                        value_ru = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ""

                        if not key:
                            errors.append(f"Строка {index}: Отсутствует ключ (Key)")
                            continue

                        # Логика Upsert (Update or Insert)
                        obj, created = Item.objects.update_or_create(
                            key=key,
                            defaults={
                                'value': value,
                                'value_ru': value_ru
                            }
                        )
                    except Exception as e:
                        # Ловим неожиданные ошибки парсинга
                        errors.append(f"Строка {index}: Ошибка обработки - {str(e)}")

            if errors:
                return Response({
                    "status": "warning",
                    "message": "Импорт завершен с ошибками",
                    "errors": errors
                }, status=status.HTTP_207_MULTI_STATUS)

            return Response({"status": "success", "message": "Данные успешно обновлены"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)