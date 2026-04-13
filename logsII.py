import json

logs = [
    "2025-02-01 10:15:33|INFO|user=anna action=login status=success ip=10.0.0.1",
    "2025-02-01 10:17:10|ERROR|user=bob action=payment status=fail amount=120",
    "2025-02-01 10:20:01|INFO|user=anna action=logout status=success",
    "2025-02-01 10:22:45|WARNING|user=anna action=payment status=fail amount=300",
    "2025-02-01 10:30:12|ERROR|user=tom action=login status=fail ip=10.0.0.5"
]

# Парсинг

def parse_logs(lines):
    parsed = []
    for line in lines:
        parts = line.split("|")
        data = {"date": parts[0], "level": parts[1]} #проверять длину списка
        for f in parts[2].split(" "):
            k, v = f.split("=")
            data[k] = int(v) if v.isdigit() else v
        parsed.append(data)
    return parsed

# Json

def save_json(data, fname="logs.json"):
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json(fname="logs.json"):
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

# Фильтрация

def filter_logs(logs, **filters):
    return [log for log in logs if all(log.get(k) == v for k, v in filters.items())]

# Агрегации

def count_by_level(logs):
    return {lvl: sum(1 for log in logs if log["level"] == lvl) for lvl in ["INFO", "ERROR", "WARNING"]}

def count_by_user(logs):
    counts = {}
    for log in logs:
        if "user" in log:
            counts[log["user"]] = counts.get(log["user"], 0) + 1
    return counts

def sum_failed_amounts(logs):
    return sum(log.get("amount", 0) for log in logs if log.get("status") == "fail" and "amount" in log)

def get_unique_ips(logs):
    return list({log["ip"] for log in logs if "ip" in log})

# Вывод

def print_logs(title, logs_list):
    print(f"\n---- {title} ----")
    for log in logs_list:
        print(log)

# Программа
#main()
parsed = parse_logs(logs)
save_json(parsed)

print_logs("FAIL ONLY", filter_logs(parsed, status="fail"))
print_logs("ONLY ERRORS", filter_logs(parsed, level="ERROR"))
print_logs("ONLY anna", filter_logs(parsed, user="anna"))

levels = count_by_level(parsed)
print(f"\n---- COUNT BY LEVEL ----\n{levels['INFO']} {levels['ERROR']} {levels['WARNING']}")

print_logs("FAILED PAYMENTS (anna)", filter_logs(parsed, user="anna", status="fail", action="payment"))

print(f"\n---- АГРЕГАЦИИ ----\nПо пользователям: {count_by_user(parsed)}")
print(f"Сумма failed платежей: {sum_failed_amounts(parsed)}")
print(f"Уникальные IP: {get_unique_ips(parsed)}")

print(f"\n---- ЗАГРУЗКА ИЗ JSON ----\nЗагружено {len(load_json())} записей")
