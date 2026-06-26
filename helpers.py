import json

DB_FILE = "database.json"

def load_data():
    """Hämtar all data från json-filen"""
    with open(DB_FILE, "r") as file:
        return json.load(file)

def save_data(data):
    """Sparar all data till json-filen"""
    with open(DB_FILE, "w") as file:
        json.dump(data, file, indent=4)

def add_chore(title, family_id):
    """Funktion för att lägga till en ny syssla"""
    data = load_data()
    
    # Skapa en ny syssla (som en dictionary)
    new_chore = {
        "id": len(data["chores"]) + 1,
        "title": title,
        "family_id": family_id,
        "is_completed": False
    }
    
    data["chores"].append(new_chore)
    save_data(data)
    print(f"Sysslan '{title}' har lagts till!")

def get_chores_by_family(family_id):
    """Hämtar alla sysslor för en specifik familj"""
    data = load_data()
    # Här kan du använda en list comprehension (som du lärt dig i Python-veckan!)
    return [chore for chore in data["chores"] if chore["family_id"] == family_id]

def complete_chore(chore_id):
    """Markerar en syssla som klar"""
    data = load_data()
    for chore in data["chores"]:
        if chore["id"] == chore_id:
            chore["is_completed"] = True
            save_data(data)
            print(f"Syssla ID {chore_id} är nu markerad som klar!")
            return
    print("Hittade ingen syssla med det ID:t.")