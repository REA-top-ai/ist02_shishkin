def analyze():
    maximum = float(input("Максимум: "))
    mean = float(input("Среднее: "))
    minimum = float(input("Минимум: "))
    std_dev = float(input("Стандартное отклонение: "))
    
    diff_max = maximum - mean
    diff_min = mean - minimum
    
    print("\nРезультат анализа:")
    
    if diff_max > 5 * std_dev or diff_min > 5 * std_dev:
        print("В ваших данных имеются экстремальные значения и требуют предобработки")
    elif diff_max > 3 * std_dev or diff_min > 3 * std_dev:
        print("В ваших данных имеются выбросы и требуют предобработки")  
    else:
        print("Ваши данные пригодны для анализа")

print("=== Анализ описательной статистики ===")
analyze()