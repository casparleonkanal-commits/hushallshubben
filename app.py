from flask import Flask, render_template, request, redirect, session
from helpers import (
    add_chore, get_chores_by_family, complete_chore, get_users_by_family,
    register_user, create_family_and_make_admin, join_family_with_code,
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
    # Säkerställ att användaren är inloggad
    if "user_id" not in session:
        return redirect("/login")
        
    # Om användaren inte har kopplat en familj än, skicka till onboarding
    if not session.get("family_id"):
        return redirect("/onboarding")
        
    chores = get_chores_by_family(session["family_id"])
    users = get_users_by_family(session["family_id"])
    
    # Hämta specifik info om familjen (t.ex. namn och inbjudningskod)
    fam_res = supabase.table("families").select("*").eq("id", session["family_id"]).execute()
    family_info = fam_res.data[0] if fam_res.data else None
    
    return render_template("index.html", chores=chores, users=users, family_info=family_info)


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
                session["family_id"] = res.data[0]["family_id"]
                session["role"] = "admin"
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