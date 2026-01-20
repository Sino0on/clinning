from django import forms

class ExcelUploadForm(forms.Form):
    file = forms.FileField(label="Выберите Excel файл (.xlsx)")

    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.endswith('.xlsx'):
            raise forms.ValidationError("Разрешены только файлы формата .xlsx")
        return file