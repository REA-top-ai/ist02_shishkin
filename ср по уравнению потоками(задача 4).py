def calculate_tariff(car_brand, age, experience, reputation, traffic):    
    # Тарифы для Volkswagen Polo
    if car_brand == 1:  
        if 20 <= age <= 27:
            if 2 <= experience <= 9:
                if 1 <= reputation <= 2:
                    if 1 <= traffic <= 3:
                        return 8.0
                    elif 4 <= traffic <= 7:
                        return 8.5
                elif 3 <= reputation <= 5:
                    if 1 <= traffic <= 3:
                        return 7.5
                    elif 4 <= traffic <= 7:
                        return 7.4
        elif 27 <= age <= 34:
            if 2 <= experience <= 9:
                if 1 <= reputation <= 2:
                    if 1 <= traffic <= 3:
                        return 7.2
                elif 3 <= reputation <= 5:
                    if 1 <= traffic <= 3:
                        return 7.0
                    elif 4 <= traffic <= 7:
                        return 7.2
            elif 10 <= experience <= 15:
                if 1 <= reputation <= 2:
                    if 1 <= traffic <= 3:
                        return 6.9
                    elif 4 <= traffic <= 7:
                        return 6.7
                elif 3 <= reputation <= 5:
                    if 4 <= traffic <= 7:
                        return 6.6
    
    # Тарифы для BMW X1
    elif car_brand == 2:  
        if 20 <= age <= 27:
            if 2 <= experience <= 9:
                if 1 <= reputation <= 2:
                    if 1 <= traffic <= 3:
                        return 12.0
                    elif 4 <= traffic <= 7:
                        return 12.5
                elif 3 <= reputation <= 5:
                    if 1 <= traffic <= 3:
                        return 11.6
                    elif 4 <= traffic <= 7:
                        return 11.3
        elif 27 <= age <= 34:
            if 2 <= experience <= 9:
                if 1 <= reputation <= 2:
                    if 1 <= traffic <= 3:
                        return 11.4
                elif 3 <= reputation <= 5:
                    if 1 <= traffic <= 3:
                        return 11.7
                    elif 4 <= traffic <= 7:
                        return 11.9
            elif 10 <= experience <= 15:
                if 1 <= reputation <= 2:
                    if 1 <= traffic <= 3:
                        return 10.8
                    elif 4 <= traffic <= 7:
                        return 11.0
                elif 3 <= reputation <= 5:
                    if 4 <= traffic <= 7:
                        return 10.9
    return None

def main():
    print("=== Яндекс.Драйв: Расчет стоимости поездки ===\n")
    
    try:
        print("Выберите марку автомобиля:")
        print("1 - Volkswagen Polo")
        print("2 - BMW X1")
        car_brand = int(input("Ваш выбор (1 или 2): "))
        
        if car_brand not in [1, 2]:
            print("Ошибка: выберите 1 или 2")
            return
        
        age = int(input("\nВведите возраст водителя (20-34 лет): "))
        experience = int(input("Введите стаж вождения (2-15 лет): "))
        
        print("\nКоэффициент репутации:")
        print("1-2 - хорошая репутация (нарушений мало или нет)")
        print("3-5 - есть нарушения или ДТП")
        reputation = int(input("Введите коэффициент репутации (1-5): "))
        
        print("\nЗагруженность дорог:")
        print("1-3 - низкая/средняя загруженность")
        print("4-7 - высокая загруженность/пробки")
        traffic = int(input("Введите уровень загруженности (1-7): "))
               
        duration = float(input("\nВведите длительность поездки (в минутах): "))
        tariff = calculate_tariff(car_brand, age, experience, reputation, traffic)
        
        if tariff is None:
            print("\nИзвините, для ваших параметров не найден подходящий тариф.")
            print("Пожалуйста, проверьте введенные данные.")
        else:
            price = duration * tariff
            
            print(f"\n{'='*50}")
            print("РАСЧЕТ СТОИМОСТИ ПОЕЗДКИ")
            print(f"{'='*50}")
            
            car_name = "Volkswagen Polo" if car_brand == 1 else "BMW X1"
            print(f"Марка автомобиля: {car_name}")
            print(f"Возраст водителя: {age} лет")
            print(f"Стаж вождения: {experience} лет")
            print(f"Коэффициент репутации: {reputation}")
            print(f"Уровень загруженности: {traffic}")
            print(f"Длительность поездки: {duration} минут")
            print(f"Тариф в минуту: {tariff} руб.")
            print(f"{'='*50}")
            print(f"Стоимость вашей поездки составит {price:.2f} руб.")
            
    except ValueError:
        print("\nОшибка: пожалуйста, вводите только числа!")

if __name__ == "__main__":
    main()