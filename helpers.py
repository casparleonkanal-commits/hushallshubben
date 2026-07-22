import os
from supabase import create_client, Client
# Detta bibliotek hjälper till att läsa .env-filen automatiskt
from dotenv import load_dotenv

# Läs in miljövariablerna från .env
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# Starta Supabase-klienten som vi använder för att prata med databasen
supabase: Client = create_client(url, key)

def add_chore(title, family_id, assigned_to=None):
    """Lägger till en ny syssla och kopplar den till en familj och eventuellt en användare"""
    # Om assigned_to är en tom sträng eller saknas, spara som None (NULL i SQL)
    user_id = int(assigned_to) if assigned_to else None

    data, count = supabase.table("chores").insert({
        "title": title,
        "family_id": family_id,
        "assigned_to": user_id
    }).execute()
    return data

def get_chores_by_family(family_id):
    """Hämtar alla sysslor för en specifik familj och inkluderar namnet på den tilldelade användaren"""
    # Vi hämtar allt (*), samt namnet från den länkade users-tabellen
    response = supabase.table("chores").select("*, users(name)").eq("family_id", family_id).execute()
    return response.data

def complete_chore(chore_id):
    """Markerar en syssla som klar (is_completed = True) i Supabase"""
    data, count = supabase.table("chores").update({
        "is_completed": True
    }).eq("id", chore_id).execute()
    print(f"Syssla ID {chore_id} är nu markerad som klar live!")
    return data

def get_users_by_family(family_id):
    """Hämtar alla familjemedlemmar från Supabase"""
    response = supabase.table("users").select("*").eq("family_id", family_id).execute()
    return response.data

import secrets
import string
from werkzeug.security import generate_password_hash, check_password_hash

# ... (din gamla kod här) ...

def generate_invite_code():
    """Genererar en slumpmässig kod på 6 tecken, t.ex. HH-X92F"""
    chars = string.ascii_uppercase + string.digits
    code = "".join(secrets.choice(chars) for _ in range(6))
    return f"HH-{code}"

def register_user(name, email, password):
    """Registrerar en ny användare utan familj"""
    hashed_pw = generate_password_hash(password)
    try:
        response = supabase.table("users").insert({
            "name": name,
            "email": email,
            "password_hash": hashed_pw,
            "role": "member" # Standardroll
        }).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Registreringsfel: {e}")
        return None

def create_family_and_make_admin(family_name, user_id):
    """Skapar en ny familj och sätter användaren som admin för den"""
    code = generate_invite_code()
    
    # 1. Skapa familjen
    family_resp = supabase.table("families").insert({
        "family_name": family_name,
        "invite_code": code
    }).execute()
    
    if not family_resp.data:
        return None
        
    family_id = family_resp.data[0]["id"]
    
    # 2. Uppdatera användaren till att tillhöra familjen och bli 'admin'
    supabase.table("users").update({
        "family_id": family_id,
        "role": "admin"
    }).eq("id", user_id).execute()
    
    return code

def join_family_with_code(invite_code, user_id):
    """Låter en användare gå med i en familj via en inbjudningskod"""
    # 1. Hitta familjen med koden
    family_resp = supabase.table("families").select("id").eq("invite_code", invite_code).execute()
    
    if not family_resp.data:
        return False # Koden fanns inte
        
    family_id = family_resp.data[0]["id"]
    
    # 2. Koppla användaren till familjen (som vanlig 'member')
    supabase.table("users").update({
        "family_id": family_id,
        "role": "member"
    }).eq("id", user_id).execute()
    
    return True

from supabase import create_client
import os

# Initiera din Supabase-klient här (eller importera den om du redan har den i helpers)
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

def setup_base_chores(family_id):
    """
    Skapar automatiskt de 4 bassyslorna med standardkonfigurationer
    för en nyregistrerad familj.
    """
    try:
        # ==========================================
        # 1. CYKELSYSTEMET (Diskmaskin & Tvättmaskin)
        # ==========================================
        
        # Skapa Diskmaskin
        dish_chore = supabase.table("permanent_chores").insert({
            "family_id": family_id,
            "title": "Diskmaskin",
            "system_type": "cycle",
            "current_status": "dirty"
        }).execute()
        
        if dish_chore.data:
            dish_id = dish_chore.data[0]["id"]
            # Lägg till standardprogram för disk
            supabase.table("chore_programs").insert([
                {"chore_id": dish_id, "name": "Eco 45°", "duration_minutes": 160},
                {"chore_id": dish_id, "name": "Snabb 60°", "duration_minutes": 30},
                {"chore_id": dish_id, "name": "Intensiv 70°", "duration_minutes": 140}
            ]).execute()

        # Skapa Tvättmaskin
        wash_chore = supabase.table("permanent_chores").insert({
            "family_id": family_id,
            "title": "Tvättmaskin",
            "system_type": "cycle",
            "current_status": "dirty"
        }).execute()
        
        if wash_chore.data:
            wash_id = wash_chore.data[0]["id"]
            # Lägg till standardprogram för tvätt
            supabase.table("chore_programs").insert([
                {"chore_id": wash_id, "name": "Bomull 40°", "duration_minutes": 120},
                {"chore_id": wash_id, "name": "Syntet 30°", "duration_minutes": 90},
                {"chore_id": wash_id, "name": "Snabbspolning", "duration_minutes": 15}
            ]).execute()

        # ==========================================
        # 2. INTERVALLSYSTEMET (Dammsugning & Sopor)
        # ==========================================
        
        # Skapa Dammsugning
        vacuum_chore = supabase.table("permanent_chores").insert({
            "family_id": family_id,
            "title": "Dammsugning",
            "system_type": "interval",
            "current_status": "active"
        }).execute()
        
        if vacuum_chore.data:
            vacuum_id = vacuum_chore.data[0]["id"]
            # Lägg till standardrum
            supabase.table("chore_zones").insert([
                {"chore_id": vacuum_id, "name": "Kök"},
                {"chore_id": vacuum_id, "name": "Vardagsrum"},
                {"chore_id": vacuum_id, "name": "Hall/Entré"}
            ]).execute()

        # Skapa Slänga sopor
        trash_chore = supabase.table("permanent_chores").insert({
            "family_id": family_id,
            "title": "Slänga sopor",
            "system_type": "interval",
            "current_status": "active"
        }).execute()
        
        if trash_chore.data:
            trash_id = trash_chore.data[0]["id"]
            # Lägg till olika sorteringar
            supabase.table("chore_zones").insert([
                {"chore_id": trash_id, "name": "Restavfall"},
                {"chore_id": trash_id, "name": "Matavfall/Kompost"},
                {"chore_id": trash_id, "name": "Plast/Kartong återvinning"}
            ]).execute()
            
        return True
    except Exception as e:
        print(f"Fel vid uppstart av bassysslor: {e}")
        return False