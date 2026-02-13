#1
sensors = {"living room": 21, "kitchen": 23, "bedroom": 20}
sensors["pantry"] = 22   

print("Датчики температуры")
print("Обновленный словарь sensors:")
for room, temp in sensors.items():
    print(f"  {room}: {temp}°C")
print()

num_cameras = {"backyard": 6, "garage": 2, "driveway": 1}

print("Камеры наружного наблюдения")
print("Исправленный словарь num_cameras:")
for location, cameras in num_cameras.items():
    print(f"  {location}: {cameras} камер")

#2
translations = {"mountain": "orod","bread": "bass","friend": "mellon","horse": "roch"}

print("Словарь переводов (Англ -> Синдарин)")
print("Словарь translations:")
print(translations)
print()

print("Переводы:")
for english, sindarin in translations.items():
    print(f"  {english} -> {sindarin}")

#3
animals_in_zoo = {}
animals_in_zoo["зебры"] = 8
animals_in_zoo["обезьяны"] = 12
animals_in_zoo["динозавры"] = 0
print(animals_in_zoo)

#4
user_ids = {"teraCoder": 9018293, "proProgrammer": 119238}

user_ids["theLooper"] = 138475
user_ids["stringQueen"] = 85739

print(user_ids)

#5
oscar_winners = {"Best Picture": "La La Land","Best Actor": "Casey Affleck","Best Actress": "Emma Stone","Animated Feature": "Zootopia"}
oscar_winners["Supporting Actress"] = "Viola Davis"
oscar_winners["Best Picture"] = "Moonlight"
print(oscar_winners)

#6
drinks = ["espresso", "chai", "decaf", "drip"]
caffeine = [64, 40, 0, 120]
zipped_drinks = zip(drinks, caffeine)
drinks_to_caffeine = {drink: mg for drink, mg in zipped_drinks}
print(drinks_to_caffeine)

#7
songs = ["Like a Rolling Stone", "Satisfaction", "Imagine", "What's Going On", "Respect", "Good Vibrations"]
playcounts = [78, 29, 44, 21, 89, 5]
plays = {song: count for song, count in zip(songs, playcounts)}
print(plays)

plays["Purple Haze"] = 1
plays["Respect"] = 94 

library = {"The Best Songs": plays, "Sunday Feelings": {}}
print(library)

