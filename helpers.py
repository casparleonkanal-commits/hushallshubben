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
        "name": family_name,
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