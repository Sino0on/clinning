"""Русский перевод надписей темы django-unfold (своего у неё нет).

Пишет locale/ru/LC_MESSAGES/django.po и компилирует django.mo в проекте.
Запуск из папки бэкенда: .venv/Scripts/python make_unfold_ru.py
"""
from pathlib import Path

import polib

T = {
    "Add new item": "Добавить",
    "Add row": "Добавить строку",
    "All applications": "Все разделы",
    "Apply Filters": "Применить фильтры",
    "Below is a preview of data to be imported. If you are satisfied with the results, click 'Confirm import'":
        "Ниже предпросмотр данных для импорта. Если всё верно, нажмите «Подтвердить импорт»",
    "Bold": "Жирный",
    "Cancel": "Отмена",
    "Change History": "История изменений",
    "Change reason": "Причина изменения",
    "Changed by": "Изменил",
    "Changes": "Изменения",
    "Choose a date from the list below to revert to a previous version of this object":
        "Выберите дату ниже, чтобы вернуть прежнюю версию",
    "Choose file to upload": "Выберите файл",
    "Click to cancel": "Нажмите, чтобы отменить",
    "Click to download": "Нажмите, чтобы скачать",
    "Code": "Код",
    "Collapse": "Свернуть",
    "Comment": "Комментарий",
    "Confirm import": "Подтвердить импорт",
    "Current file": "Текущий файл",
    "Dark": "Тёмная",
    "Dataset not found. No action performed.": "Данные не найдены, ничего не сделано.",
    "Date": "Дата",
    "Date from": "Дата с",
    "Date to": "Дата по",
    "Default": "По умолчанию",
    "Edit": "Изменить",
    "Enter an URL": "Введите ссылку",
    "Expand row": "Развернуть",
    "Export": "Экспорт",
    "False": "Нет",
    "Filters": "Фильтры",
    "Forgotten your password or username?": "Забыли пароль или логин?",
    "From": "С",
    "General": "Основное",
    "Go back": "Назад",
    "Group": "Группа",
    "Group permissions": "Права группы",
    "Heading": "Заголовок",
    "Image preview": "Просмотр картинки",
    "Import": "Импорт",
    "Indent decrease": "Уменьшить отступ",
    "Indent increase": "Увеличить отступ",
    "Italic": "Курсив",
    "Light": "Светлая",
    "Line number": "Номер строки",
    "Link": "Ссылка",
    "Loading more results...": "Загружаем ещё…",
    "Manage group": "Управление группой",
    "Manage user": "Управление пользователем",
    "More actions": "Ещё действия",
    "Name": "Название",
    "New": "Новый",
    "Next": "Далее",
    "No data": "Нет данных",
    "No recent searches": "Недавних поисков нет",
    "No results found": "Ничего не найдено",
    "No results matching your query": "По вашему запросу ничего не найдено",
    "Non field specific": "Общие ошибки",
    "Not enough data.": "Недостаточно данных.",
    "Object": "Запись",
    "Object permissions": "Права на запись",
    "Ordered list": "Нумерованный список",
    "Paragraph": "Абзац",
    "Please correct these errors in your data where possible, then reupload it using the form above.":
        "Исправьте эти ошибки в файле и загрузите его ещё раз через форму выше.",
    "Previous": "Назад",
    "Quote": "Цитата",
    "Recent searches": "Недавние поиски",
    "Record picture": "Сделать фото",
    "Redo": "Повторить",
    "Reset filters": "Сбросить фильтры",
    "Reset to default": "Сбросить",
    "Return to site": "Открыть сайт",
    "Revert": "Вернуть",
    "Row": "Строка",
    "Run": "Выполнить",
    "Search apps and models...": "Поиск по разделам…",
    "Select action": "Выберите действие",
    "Select action to run": "Выберите действие",
    "Select all rows": "Отметить все",
    "Select currency": "Выберите валюту",
    "Select format": "Выберите формат",
    "Select record": "Отметить",
    "Select value": "Выберите значение",
    "Skipped": "Пропущено",
    "Some rows failed to validate": "В некоторых строках ошибки",
    "Strike": "Зачёркнутый",
    "Submit": "Отправить",
    "System": "Как в системе",
    "This exporter will export the following fields": "Будут выгружены поля",
    "This exporter will export the following fields: ": "Будут выгружены поля: ",
    "This importer will import the following fields: ": "Будут загружены поля: ",
    "This item will be deleted.": "Эта запись будет удалена.",
    "This object doesn't have a change history.": "У этой записи нет истории изменений.",
    "This object doesn’t have a change history. It probably wasn’t added via this admin site.":
        "У этой записи нет истории изменений. Возможно, она добавлена не через админку.",
    "This page yielded into no results. Create a new item or reset your filters.":
        "Здесь пока ничего нет. Добавьте запись или сбросьте фильтры.",
    "To": "По",
    "Toggle password visibility": "Показать или скрыть пароль",
    "True": "Да",
    "Type to search": "Поиск",
    "Underlined": "Подчёркнутый",
    "Undo": "Отменить",
    "Unlink": "Убрать ссылку",
    "Unordered list": "Маркированный список",
    "Update": "Обновить",
    "User permissions": "Права пользователя",
    "Value": "Значение",
    "View traceback": "Подробности ошибки",
    "Welcome": "Здравствуйте",
    "You can not create nested object without parent": "Нельзя создать вложенную запись без основной",
    "You have been successfully logged out from the administration": "Вы вышли из админки",
}

out = Path("locale/ru/LC_MESSAGES")
out.mkdir(parents=True, exist_ok=True)
po = polib.POFile()
po.header = (
    "Русский перевод надписей темы админки django-unfold (своего у неё нет).\n"
    "После правок перекомпилировать django.mo, например:\n"
    "python -c \"import polib; polib.pofile('locale/ru/LC_MESSAGES/django.po')"
    ".save_as_mofile('locale/ru/LC_MESSAGES/django.mo')\""
)
po.metadata = {
    "Project-Id-Version": "clinning",
    "Language": "ru",
    "MIME-Version": "1.0",
    "Content-Type": "text/plain; charset=UTF-8",
    "Content-Transfer-Encoding": "8bit",
    "Plural-Forms": "nplurals=4; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && "
                    "(n%100<12 || n%100>14) ? 1 : n%10==0 || (n%10>=5 && n%10<=9) || "
                    "(n%100>=11 && n%100<=14)? 2 : 3);",
}
for msgid, msgstr in T.items():
    po.append(polib.POEntry(msgid=msgid, msgstr=msgstr))
po.save(out / "django.po")
po.save_as_mofile(out / "django.mo")
print(f"{len(T)} строк -> {out}/django.po + django.mo")
