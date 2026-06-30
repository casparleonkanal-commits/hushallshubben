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

def add_chore(title, family_id):
    """Lägger till en ny syssla i Supabase-databasen"""
    data, count = supabase.table("chores").insert({
        "title": title,
        "family_id": family_id
    }).execute()
    print(f"Sysslan '{title}' har sparats live i molnet!")
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