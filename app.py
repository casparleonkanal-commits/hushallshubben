from flask import Flask, render_template, request, redirect
from helpers import add_chore, get_chores_by_family

app = Flask(__name__)

# Vi låtsas att vi är inloggade som familj ID 1 just nu
CURRENT_FAMILY_ID = 1

@app.route("/")
def index():
    # 1. Hämta alla sysslor live från Supabase via din helpers-fil
    chores = get_chores_by_family(CURRENT_FAMILY_ID)
    
    # 2. Skicka sysslorna till HTML-mallen
    return render_template("index.html", chores=chores)

@app.route("/add", methods=["POST"])
def add():
    # 1. Fånga upp vad användaren skrev i formuläret
    title = request.form.get("title")
    
    # 2. Om textfältet inte var tomt, spara i Supabase
    if title:
        add_chore(title, CURRENT_FAMILY_ID)
        
    # 3. Skicka tillbaka användaren till startsidan
    return redirect("/")