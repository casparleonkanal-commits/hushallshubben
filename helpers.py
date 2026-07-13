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
    """Hämtar alla sysslor för en specifik familj från Supabase"""
    response = supabase.table("chores").select("*").eq("family_id", family_id).execute()
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