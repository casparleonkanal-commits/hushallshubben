from flask import Flask, render_template, request, redirect, session, url_for
from helpers import (
    add_chore, get_chores_by_family, complete_chore, get_users_by_family,
    register_user, create_family_and_make_admin, join_family_with_code, setup_base_chores,
    supabase
)
from werkzeug.security import check_password_hash
import os
from dotenv import load_dotenv

# Läs in miljövariabler från .env
load_dotenv()

app = Flask(__name__)

# Hemlig nyckel för kryptering av sessionscookies
app.secret_key = os.getenv("FLASK_SECRET_KEY", "en-super-hemlig-test-nyckel-123")


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")
    if not session.get("family_id"):
        return redirect("/onboarding")
        
    chores = get_chores_by_family(session["family_id"])
    users = get_users_by_family(session["family_id"])
    
    fam_res = supabase.table("families").select("*").eq("id", session["family_id"]).execute()
    family_info = fam_res.data[0] if fam_res.data else None
    
    # Hämta de permanenta sysslorna med program och zoner
   # Använd parentes runt hela uttrycket istället för backslash
    perm_res = (
        supabase.table("permanent_chores")
        .select("*, chore_programs!chore_programs_chore_id_fkey(*), chore_zones(*)")
        .eq("family_id", session["family_id"])
        .execute()
    )
    permanent_chores = perm_res.data if perm_res.data else []
    
    # TIDSBEHANDLING FÖR MASKINER
    now = datetime.now(timezone.utc)
    
    for chore in permanent_chores:
        if chore["system_type"] == "cycle" and chore["current_status"] == "running":
            # Hitta vilket program som körs
            active_prog = next((p for p in chore["chore_programs"] if p["id"] == chore["active_program_id"]), None)
            
            if active_prog and chore["timer_started_at"]:
                # Gör om strängen från Supabase till ett datetime-objekt i UTC
                started_at = datetime.fromisoformat(chore["timer_started_at"].replace("Z", "+00:00"))
                
                # Räkna ut hur många minuter maskinen har kört
                elapsed_minutes = (now - started_at).total_seconds() / 60
                duration = active_prog["duration_minutes"]
                
                if elapsed_minutes >= duration:
                    # Tiden har gått ut! Uppdatera statusen direkt i databasen och i vårt lokala objekt
                    supabase.table("permanent_chores").update({"current_status": "ready"}).eq("id", chore["id"]).execute()
                    chore["current_status"] = "ready"
                    chore["remaining_minutes"] = 0
                else:
                    # Maskinen körs fortfarande, spara hur många minuter som är kvar
                    chore["remaining_minutes"] = int(duration - elapsed_minutes)
                    
    return render_template(
        "index.html", 
        chores=chores, 
        users=users, 
        family_info=family_info,
        permanent_chores=permanent_chores
    )


@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session or not session.get("family_id"):
        return redirect("/login")
        
    title = request.form.get("title")
    assigned_to = request.form.get("assigned_to") # Fånga upp vem sysslan gavs till
    
    if title:
        add_chore(title, session["family_id"], assigned_to)
        
    return redirect("/")


@app.route("/complete/<int:chore_id>", methods=["POST"])
def complete(chore_id):
    if "user_id" not in session:
        return redirect("/login")
        
    complete_chore(chore_id)
    return redirect("/")

from datetime import datetime, timezone

@app.route("/perm/start_machine/<int:chore_id>", methods=["POST"])
def start_machine(chore_id):
    if "user_id" not in session or not session.get("family_id"):
        return redirect("/login")
        
    program_id = request.form.get("program_id")
    if not program_id:
        return "Inget program valt", 400
        
    # Starta timern i databasen med nuvarande tidstämpel (UTC) och ändra status till running
    supabase.table("permanent_chores").update({
        "current_status": "running",
        "active_program_id": int(program_id),
        "timer_started_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", chore_id).execute()
    
    return redirect("/")


@app.route("/perm/reset_machine/<int:chore_id>", methods=["POST"])
def reset_machine(chore_id):
    if "user_id" not in session:
        return redirect("/login")
        
    # När maskinen är tömd går den tillbaka till att vara smutsig, och timern nollställs
    supabase.table("permanent_chores").update({
        "current_status": "dirty",
        "active_program_id": None,
        "timer_started_at": None
    }).eq("id", chore_id).execute()
    
    return redirect("/")


@app.route("/perm/reset_zone/<int:zone_id>", methods=["POST"])
def reset_zone(zone_id):
    if "user_id" not in session:
        return redirect("/login")
        
    # Uppdatera zonen till att ha blivit städad/tömd precis just nu av denna användare
    supabase.table("chore_zones").update({
        "last_cleared_at": datetime.now(timezone.utc).isoformat(),
        "last_cleared_by": session["user_id"]
    }).eq("id", zone_id).execute()
    
    return redirect("/")

@app.route("/perm/add_program/<int:chore_id>", methods=["POST"])
def add_program(chore_id):
    if session.get("role") != "admin":
        return "Endast admin har tillgång till inställningar.", 403
        
    name = request.form.get("name")
    duration = request.form.get("duration_minutes")
    
    if name and duration:
        supabase.table("chore_programs").insert({
            "chore_id": chore_id,
            "name": name,
            "duration_minutes": int(duration)
        }).execute()
        
    return redirect("/")


@app.route("/perm/add_zone/<int:chore_id>", methods=["POST"])
def add_zone(chore_id):
    if session.get("role") != "admin":
        return "Endast admin har tillgång till inställningar.", 403
        
    name = request.form.get("name")
    if name:
        supabase.table("chore_zones").insert({
            "chore_id": chore_id,
            "name": name
        }).execute()
        
    return redirect("/")
@app.route('/perm/delete_program/<int:program_id>', methods=['POST'])
def delete_program(program_id):
    # Ändra till ditt tabellnamn om det heter något annat
    supabase.table('chore_programs').delete().eq('id', program_id).execute()
    return redirect(url_for('index'))

@app.route('/perm/delete_zone/<int:zone_id>', methods=['POST'])
def delete_zone(zone_id):
    # Ändra till ditt tabellnamn om det heter något annat
    supabase.table('chore_zones').delete().eq('id', zone_id).execute()
    return redirect(url_for('index'))

@app.route("/delete/<int:chore_id>", methods=["POST"])
def delete_chore_route(chore_id):
    # Säkerhetskontroll: Endast admin får ta bort saker helt
    if session.get("role") != "admin":
        return "Behörighet saknas. Endast familjens administratör kan radera sysslor.", 403
        
    supabase.table("chores").delete().eq("id", chore_id).execute()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        
        user = register_user(name, email, password)
        if user:
            # Sätt sessionen direkt efter lyckad registrering
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]
            session["family_id"] = user["family_id"]
            return redirect("/onboarding")
        else:
            return "Registreringen misslyckades. E-postadressen kanske redan används.", 400
            
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Sök efter användaren i databasen via e-post
        res = supabase.table("users").select("*").eq("email", email).execute()
        if res.data:
            user = res.data[0]
            # Verifiera det hashade lösenordet
            if check_password_hash(user["password_hash"], password):
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                session["role"] = user["role"]
                session["family_id"] = user["family_id"]
                
                # Om kontot saknar familjekoppling skickas man till onboarding-valet
                if not user["family_id"]:
                    return redirect("/onboarding")
                return redirect("/")
                
        return "Fel e-post eller lösenord", 401
        
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear() # Rensa webbläsarsessionen helt och hållet
    return redirect("/login")


@app.route("/onboarding", methods=["GET", "POST"])
def onboarding():
    if "user_id" not in session:
        return redirect("/login")
        
    if request.method == "POST":
        action = request.form.get("action")
        user_id = session["user_id"]
        
        if action == "create":
            family_name = request.form.get("family_name")
            invite_code = create_family_and_make_admin(family_name, user_id)
            if invite_code:
                # Synka om sessionen med den nya datan från Supabase
                res = supabase.table("users").select("*").eq("id", user_id).execute()
                
                new_family_id = res.data[0]["family_id"]
                session["family_id"] = new_family_id
                session["role"] = "admin"
                
                # ==========================================
                # HÄR TRIPPAS BASSYSSLORNA IGÅNG!
                # ==========================================
                if new_family_id:
                    setup_base_chores(new_family_id)
                
                return redirect("/")
                
        elif action == "join":
            code = request.form.get("invite_code").strip().upper()
            if join_family_with_code(code, user_id):
                # Synka om sessionen med den nya datan från Supabase
                res = supabase.table("users").select("*").eq("id", user_id).execute()
                session["family_id"] = res.data[0]["family_id"]
                session["role"] = "member"
                return redirect("/")
            else:
                return "Felaktig inbjudningskod.", 400
                
    return render_template("onboarding.html")