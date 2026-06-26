from helpers import add_chore, get_chores_by_family, complete_chore

# 1. Vi låtsas att "Familjen Andersson" har ID 101. Vi lägger till två sysslor.
print("--- Testar att lägga till sysslor ---")
add_chore("Diska köket", 101)
add_chore("Gå ut med soporna", 101)
add_chore("Klippa gräset i Nynäs", 102) # Denna tillhör en annan familj!

# 2. Vi hämtar sysslor för familj 101 för att se att det funkar
print("\n--- Hämtar sysslor för familj 101 ---")
anderssons_chores = get_chores_by_family(101)
for chore in anderssons_chores:
    status = "KLAR" if chore["is_completed"] else "ATT GÖRA"
    print(f"[{status}] ID: {chore['id']} - {chore['title']}")

# 3. Vi testar att bocka av en syssla
print("\n--- Testar att bocka av en syssla ---")
complete_chore(1)

# 4. Vi kollar listan igen för att se att statusen ändrades
print("\n--- Hämtar listan igen efter uppdatering ---")
for chore in get_chores_by_family(101):
    status = "KLAR" if chore["is_completed"] else "ATT GÖRA"
    print(f"[{status}] ID: {chore['id']} - {chore['title']}")