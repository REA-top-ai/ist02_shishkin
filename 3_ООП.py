from functools import wraps

# ДЕКОРАТОРЫ 

def is_alive(func):
    """Декоратор проверяет, жив ли герой (health > 0). Если нет — выводит сообщение и не вызывает метод."""
    @wraps(func)
    def wrapper(hero_instance, *args, **kwargs):
        if hero_instance.health <= 0:
            print(f"{hero_instance.name} мертв и не может действовать!")
            return None
        return func(hero_instance, *args, **kwargs)
    return wrapper


def log_action(func):
    """Декоратор логирует начало и конец выполнения метода."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[LOG] Начало действия: {func.__name__}")
        result = func(*args, **kwargs)
        print(f"[LOG] Действие завершено")
        return result
    return wrapper


def double_health_and_half_mana_buff(duration_func):
    """
    Декоратор для временного увеличения здоровья вдвое и маны в 1.5 раза.
    Применяется к функции, которая запускает праздничный ивент.
    """
    @wraps(duration_func)
    def wrapper(hero_instance, *args, **kwargs):
        # Сохраняем исходные значения
        original_health = hero_instance.health
        original_max_health = getattr(hero_instance, 'max_health', hero_instance.health)
        original_mana = hero_instance.mana
        
        # Применяем бафф
        hero_instance.health = original_health * 2
        hero_instance.mana = int(original_mana * 1.5)
        # Сохраняем новую максимальную здоровье для возможных проверок
        hero_instance.max_health = original_max_health * 2
        
        print(f"[ПРАЗДНИК] У {hero_instance.name} здоровье увеличено вдвое ({hero_instance.health}), мана увеличена в 1.5 раза ({hero_instance.mana})")
        
        # Выполняем основную функцию (например, продолжительность ивента)
        result = duration_func(hero_instance, *args, **kwargs)
        
        # Откатываем изменения (ивент закончился)
        hero_instance.health = original_health
        hero_instance.mana = original_mana
        if hasattr(hero_instance, 'max_health'):
            del hero_instance.max_health
        
        print(f"[ПРАЗДНИК] Эффект праздника закончился. Здоровье и мана {hero_instance.name} восстановлены.")
        return result
    return wrapper


def add_sacred_staff_for_wizard(duration_func):
    """
    Декоратор временно добавляет волшебнику предмет 'Священный посох' (+5 к мане).
    Для воина ничего не меняется.
    """
    @wraps(duration_func)
    def wrapper(hero_instance, *args, **kwargs):
        if hero_instance.hero_class == "волшебник":
            # Добавляем временный предмет
            temp_item = {
                "Священный посох": {"мана": 5}
            }
            hero_instance.items.update(temp_item)
            hero_instance.mana += 5
            print(f"[ПРЕДМЕТ] Волшебник {hero_instance.name} получил 'Священный посох' (+5 маны). Теперь маны: {hero_instance.mana}")
        else:
            print(f"[ПРЕДМЕТ] {hero_instance.name} — воин, 'Священный посох' ему не нужен.")
        
        result = duration_func(hero_instance, *args, **kwargs)
        
        # Убираем временный предмет
        if hero_instance.hero_class == "волшебник" and "Священный посох" in hero_instance.items:
            hero_instance.mana -= 5
            del hero_instance.items["Священный посох"]
            print(f"[ПРЕДМЕТ] 'Священный посох' исчез. Мана {hero_instance.name} вернулась к {hero_instance.mana}")
        
        return result
    return wrapper


def solar_crest_shield(func):
    """
    ДЕКОРАТОР ИЗ DOTA 2 — SOLAR CREST (Соляной Гребень).
    Добавляет герою щит перед выполнением метода.
    Формула щита: 100 + 0.5 * (максимальное здоровье героя).
    Щит поглощает урон, уменьшая здоровье героя только если урон превышает щит.
    """
    @wraps(func)
    def wrapper(hero_instance, damage, *args, **kwargs):
        # Рассчитываем щит
        max_hp = getattr(hero_instance, 'max_health', hero_instance.health)
        shield_value = 100 + 0.5 * max_hp
        shield_value = int(shield_value)  # на всякий случай
        
        # Сохраняем текущий щит в атрибут (если его еще нет)
        if not hasattr(hero_instance, 'shield'):
            hero_instance.shield = 0
        
        # Добавляем новый щит (в Dota 2 эффект не суммируется, но для примера суммируем)
        hero_instance.shield += shield_value
        print(f"[SOLAR CREST] {hero_instance.name} получает щит {shield_value}. Общий щит: {hero_instance.shield}")
        
        # Модифицируем урон: сначала щит, потом здоровье
        absorbed = min(hero_instance.shield, damage)
        hero_instance.shield -= absorbed
        remaining_damage = damage - absorbed
        
        if remaining_damage > 0:
            # Применяем оставшийся урон к здоровью
            print(f"[SOLAR CREST] Щит поглотил {absorbed} урона. Остаток урона {remaining_damage} идет по здоровью.")
            # Временно убираем декоратор is_alive, чтобы избежать блокировки
            # Но здесь мы просто вызываем оригинальную атаку напрямую с модифицированным уроном
            original_health = hero_instance.health
            hero_instance.health -= remaining_damage
            print(f"Герой {hero_instance.name} получил {remaining_damage} урона. Здоровье: {hero_instance.health}")
            return func(hero_instance, 0)  # вызываем оригинальный метод с 0 урона (уже нанесли)
        else:
            print(f"[SOLAR CREST] Щит полностью поглотил урон {damage}. Здоровье не пострадало.")
            return func(hero_instance, 0)
    
    return wrapper


# КЛАСС HERO 

class Hero:
    def __init__(self, name, hero_class):
        self.name = name
        self.hero_class = hero_class
        
        if hero_class == "волшебник":
            self.health = 60
            self.mana = 50
        elif hero_class == "воин":
            self.health = 100
            self.mana = 10
        else:
            raise ValueError("hero_class должен быть 'волшебник' или 'воин'")
        
        self.spells_names = {}  # словарь заклинаний
        self.items = {}         # словарь предметов
    
    @is_alive
    def attack(self, damage):
        """Атака врага (отнимает здоровье у врага, но в этой версии просто выводит урон)."""
        print(f"Герой {self.name} нанес урон: {damage}")
    
    @log_action
    def heal(self, amount):
        """Восстанавливает здоровье герою."""
        self.health += amount
        print(f"Герой {self.name} восстановил {amount} здоровья. Текущее здоровье: {self.health}")
    
    @is_alive
    def cast_spell(self, spell_name):
        """Использование заклинания: тратит ману, выводит название."""
        if spell_name not in self.spells_names:
            print(f"Заклинание {spell_name} не изучено!")
            return
        
        spell = self.spells_names[spell_name]
        mana_cost = spell.get("mana_cost", 0)
        
        if self.mana < mana_cost:
            print(f"Недостаточно маны для заклинания {spell_name}!")
            return
        
        self.mana -= mana_cost
        print(f"Герой {self.name} применил заклинание '{spell_name}'. Потрачено маны: {mana_cost}. Осталось маны: {self.mana}")
        
        # Применяем эффекты заклинания
        if "attack_damage" in spell:
            print(f"  -> Урон врагу: {spell['attack_damage']}")
        if "health_increase" in spell:
            self.health += spell["health_increase"]
            print(f"  -> Восстановлено здоровья: {spell['health_increase']}. Текущее здоровье: {self.health}")
    
    def add_spell(self, spell_name, mana_cost, attack_damage=0, health_increase=0):
        """Добавляет новое заклинание в словарь."""
        self.spells_names[spell_name] = {
            "mana_cost": mana_cost,
            "attack_damage": attack_damage,
            "health_increase": health_increase
        }
        print(f"Герой {self.name} изучил заклинание '{spell_name}'.")
    
    def add_item(self, item_name, param, value):
        """Добавляет предмет. param: 'здоровье' или 'мана'."""
        if len(self.items) >= 6:
            print("Слишком много предметов! Максимум 6.")
            return
        
        self.items[item_name] = {param: value}
        
        # Применяем эффект предмета
        if param == "здоровье":
            self.health += value
            print(f"Предмет {item_name} добавлен. Здоровье увеличено на {value}. Теперь: {self.health}")
        elif param == "мана":
            self.mana += value
            print(f"Предмет {item_name} добавлен. Мана увеличена на {value}. Теперь: {self.mana}")
    
    def __str__(self):
        return f"Hero {self.name} ({self.hero_class}): HP={self.health}, MP={self.mana}, Items={list(self.items.keys())}"

# ПРИМЕР ИСПОЛЬЗОВАНИЯ 

if __name__ == "__main__":
    # Создаем героя Джакиро (волшебник)
    jakiro = Hero("Джакиро", "волшебник")
    print(jakiro)
    
    # Добавляем заклинания
    jakiro.add_spell("Огненная стена", mana_cost=20, attack_damage=35)
    jakiro.add_spell("Ледяной путь", mana_cost=25, attack_damage=40, health_increase=10)
    
    # Добавляем обычный предмет
    jakiro.add_item("Мантийка интеллекта", "мана", 10)
    print(jakiro)
    
    print("\n" + "="*50)
    print("ПРОВЕРКА ДЕКОРАТОРОВ is_alive И log_action")
    print("="*50)
    
    # Атака
    jakiro.attack(25)
    
    # Лечение (логгируется)
    jakiro.heal(20)
    
    # Применение заклинания
    jakiro.cast_spell("Огненная стена")
    
    # Убиваем героя
    print("\n--- Наносим смертельный урон ---")
    jakiro.health = 0
    print(f"{jakiro.name} теперь мертв (HP=0)")
    jakiro.attack(10)       # не сработает из-за is_alive
    jakiro.cast_spell("Ледяной путь")  # не сработает
    
    print("\n" + "="*50)
    print("ПРОВЕРКА ПРАЗДНИЧНЫХ ДЕКОРАТОРОВ")
    print("="*50)
    
    # Воскрешаем для теста
    jakiro.health = 60
    jakiro.mana = 50
    print(f"После воскрешения: {jakiro}")
    
    # Декоратор для ивента (увеличение здоровья и маны)
    @double_health_and_half_mana_buff
    def easter_event(hero):
        print(f"ИВЕНТ: {hero.name} участвует в пасхальном ивенте!")
        hero.attack(15)
        hero.cast_spell("Огненная стена")
        return "Ивент прошел успешно"
    
    easter_event(jakiro)
    print(f"После ивента: {jakiro}")
    
    print("\n" + "="*50)
    print("ПРОВЕРКА ДЕКОРАТОРА add_sacred_staff_for_wizard")
    print("="*50)
    
    @add_sacred_staff_for_wizard
    def wizard_event(hero):
        print(f"Волшебник {hero.name} получает священный посох на время ивента")
        hero.cast_spell("Ледяной путь")
        return "OK"
    
    wizard_event(jakiro)
    print(f"После ивента с посохом: {jakiro}")
    
    print("\n" + "="*50)
    print("ПРОВЕРКА ДЕКОРАТОРА SOLAR CREST (ЩИТ ИЗ DOTA 2)")
    print("="*50)
    
    # Создаем нового героя для чистоты теста
    sven = Hero("Свен", "воин")
    print(sven)
    
    # Применяем декоратор Solar Crest к методу attack
    @solar_crest_shield
    def shielded_attack(hero, damage):
        hero.attack(damage)
    
    print("\n--- Свен получает щит Solar Crest и атакует ---")
    shielded_attack(sven, 50)   # Урон 50, щит должен полностью поглотить (100 + 50 = 150 щита)
    
    print("\n--- Свен получает второй щит (суммируется) и сильный удар ---")
    shielded_attack(sven, 180)  # Щит был 100 (остаток от прошлого) + новый щит 150 = 250, поглотит 180
    
    print("\n--- Проверяем, что здоровье не изменилось (щит сработал) ---")
    print(sven)  # Здоровье должно быть 100