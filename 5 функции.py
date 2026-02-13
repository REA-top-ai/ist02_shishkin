def create_spreadsheet(title):
    print("Создание электронной таблицы с именем " + title)

create_spreadsheet("Загрузки")
print("\n После добавления row_count\n")

def create_spreadsheet(title, row_count=1000):
    print("Создание электронной таблицы с названием " + title + " with " + str(row_count) + " lines")

create_spreadsheet("Приложения", 10)

print("\n Проверка значения по умолчанию")

create_spreadsheet("Отчет")