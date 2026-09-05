"""
Xorazm pedagogika texnikumi elektron kutubxonasi - Web versiya (Flask)
"""
from flask import Flask, render_template_string, request, redirect, url_for
import json
import os

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "kutubxona.json")

BO_LIMLAR = [
    "Umumta'lim fanlar",
    "Umumkasbiy fanlar",
    "Maxsus fanlar",
    "Badiiy adabiyotlar",
]


def yuklash():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {b: [] for b in BO_LIMLAR}


def saqlash(malumot):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(malumot, f, ensure_ascii=False, indent=2)


HTML = """
<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<title>Xorazm Pedagogika Texnikumi Kutubxonasi</title>
<style>
  body { font-family: 'Segoe UI', sans-serif; background: #f4f6fa; margin: 0; padding: 20px; }
  .container { max-width: 900px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
  h1 { color: #1a3a6e; text-align: center; margin-bottom: 5px; }
  h2 { color: #1a3a6e; }
  .subtitle { text-align: center; color: #666; margin-bottom: 30px; }
  .bolim { background: #eef3ff; padding: 20px; margin: 15px 0; border-radius: 10px; border-left: 5px solid #1a3a6e; }
  .bolim h2 { margin-top: 0; }
  .kitob { background: #fff; padding: 10px 15px; margin: 5px 0; border-radius: 6px; border: 1px solid #e0e0e0; }
  form { background: #f8faff; padding: 15px; border-radius: 8px; margin: 15px 0; }
  input, select, button { padding: 8px; margin: 5px 0; border-radius: 6px; border: 1px solid #ccc; }
  button { background: #1a3a6e; color: #fff; border: none; cursor: pointer; padding: 10px 20px; }
  button:hover { background: #2a5aa0; }
  .search { margin: 15px 0; }
  .result { background: #e8f5e9; padding: 10px; border-radius: 6px; margin: 5px 0; }
  .nav { text-align: center; margin: 20px 0; }
  .nav a { color: #1a3a6e; margin: 0 10px; text-decoration: none; font-weight: bold; }
</style>
</head>
<body>
<div class="container">
  <h1>Xorazm Pedagogika Texnikumi</h1>
  <h2>Elektron Kutubxona</h2>
  <p class="subtitle">Barcha fanlar va badiiy adabiyotlar bir joyda</p>

  <div class="nav">
    <a href="{{ url_for('bosh_sahifa') }}">Bosh sahifa</a>
    <a href="{{ url_for('qidirish') }}">Qidirish</a>
    <a href="{{ url_for('qoshish') }}">Kitob qo'shish</a>
  </div>

  {% if sahifa == 'bosh' %}
    {% for bolim in bolimlar %}
    <div class="bolim">
      <h2>{{ bolim }}</h2>
      <p>{{ malumot[bolim]|length }} ta kitob</p>
      {% if malumot[bolim] %}
        {% for kitob in malumot[bolim] %}
        <div class="kitob">
          <b>{{ kitob.nomi }}</b> — {{ kitob.muallif }} ({{ kitob.yili }})
        </div>
        {% endfor %}
      {% else %}
        <p>Bu bo'limda kitob yo'q.</p>
      {% endif %}
    </div>
    {% endfor %}

  {% elif sahifa == 'qidirish' %}
    <form method="get">
      <input type="text" name="so_rov" placeholder="Kitob yoki muallif..." value="{{ so_rov or '' }}" style="width: 70%;">
      <button type="submit">Qidirish</button>
    </form>
    {% if natija is not none %}
      {% if natija %}
        {% for item in natija %}
        <div class="result">
          <b>[{{ item.bolim }}]</b> {{ item.kitob.nomi }} — {{ item.kitob.muallif }} ({{ item.kitob.yili }})
        </div>
        {% endfor %}
      {% else %}
        <p>Hech narsa topilmadi.</p>
      {% endif %}
    {% endif %}

  {% elif sahifa == 'qoshish' %}
    <form method="post">
      <label>Bo'lim:</label><br>
      <select name="bolim" style="width: 100%;">
        {% for bolim in bolimlar %}
          <option value="{{ bolim }}">{{ bolim }}</option>
        {% endfor %}
      </select><br>
      <label>Kitob nomi:</label><br>
      <input type="text" name="nomi" required style="width: 100%;"><br>
      <label>Muallif:</label><br>
      <input type="text" name="muallif" required style="width: 100%;"><br>
      <label>Yili:</label><br>
      <input type="text" name="yili" required style="width: 100%;"><br>
      <button type="submit">Saqlash</button>
    </form>
  {% endif %}
</div>
</body>
</html>
"""


@app.route("/")
def bosh_sahifa():
    return render_template_string(HTML, sahifa="bosh", bolimlar=BO_LIMLAR, malumot=yuklash())


@app.route("/qidirish")
def qidirish():
    so_rov = request.args.get("so_rov", "").strip().lower()
    natija = None
    if so_rov:
        natija = []
        for bolim, kitoblar in yuklash().items():
            for kitob in kitoblar:
                if so_rov in kitob["nomi"].lower() or so_rov in kitob["muallif"].lower():
                    natija.append({"bolim": bolim, "kitob": kitob})
    return render_template_string(HTML, sahifa="qidirish", bolimlar=BO_LIMLAR, so_rov=so_rov, natija=natija)


@app.route("/qoshish", methods=["GET", "POST"])
def qoshish():
    if request.method == "POST":
        m = yuklash()
        m[request.form["bolim"]].append({
            "nomi": request.form["nomi"],
            "muallif": request.form["muallif"],
            "yili": request.form["yili"],
        })
        saqlash(m)
        return redirect(url_for("bosh_sahifa"))
    return render_template_string(HTML, sahifa="qoshish", bolimlar=BO_LIMLAR, malumot=yuklash())


if __name__ == "__main__":
    app.run(debug=True)