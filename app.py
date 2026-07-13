from flask import Flask, render_template, request, redirect
from helpers import add_chore, get_chores_by_family, complete_chore, get_users_by_family

app = Flask(__name__)

# Vi låtsas att vi är inloggade som familj ID 1 just nu
CURRENT_FAMILY_ID = 1

@app.route("/")
def index():
    chores = get_chores_by_family(CURRENT_FAMILY_ID)
    # Hämta användarna live från Supabase
    users = get_users_by_family(CURRENT_FAMILY_ID)

    # Skicka med både sysslor OCH användare till HTML
    return render_template("index.html", chores=chores, users=users)

@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title")
    assigned_to = request.form.get("assigned_to") # Fånga upp vem som blev vald

    if title:
        add_chore(title, CURRENT_FAMILY_ID, assigned_to)

    return redirect("/")

@app.route("/complete/<int:chore_id>", methods=["POST"])
def complete(chore_id):
    # 1. Kalla på din färdiga funktion i helpers.py för att uppdatera i Supabase
    complete_chore(chore_id)
    
    # 2. Skicka tillbaka användaren till startsidan så listan uppdateras
    return redirect("/")