"""
Xorazm pedagogika texnikumi elektron kutubxonasi
Foydalanuvchi tizimi bilan (ro'yxatdan o'tish, kirish, email tasdiqlash)
"""
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import random
import string

app = Flask(__name__)
app.secret_key = "maxfiy_kalit_uzgartirilsin"
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "static", "files")
app.config["COVER_FOLDER"] = os.path.join(os.path.dirname(__file__), "static", "covers")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

DATA_FILE = os.path.join(os.path.dirname(__file__), "kutubxona.json")
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

BO_LIMLAR = [
    "Umumta'lim fanlar",
    "Umumkasbiy fanlar",
    "Maxsus fanlar",
    "Badiiy adabiyotlar",
]

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["COVER_FOLDER"], exist_ok=True)


def foydalanuvchilar_yuklash():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"tasdiqlanmaganlar": {}, "faollar": {}}


def foydalanuvchilar_saqlash(f):
    with open(USERS_FILE, "w", encoding="utf-8") as fp:
        json.dump(f, fp, ensure_ascii=False, indent=2)


def kitoblar_yuklash():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {b: [] for b in BO_LIMLAR}


def kitoblar_saqlash(m):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)


def kod_yaratish():
    return "".join(random.choices(string.digits, k=6))


def email_yuborish(manzil, kod):
    """Gmail SMTP orqali tasdiqlash kodini yuboradi"""
    import smtplib
    from email.mime.text import MIMEText
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    gmail = os.getenv("GMAIL")
    parol = os.getenv("APP_PASSWORD")

    if not gmail or not parol or "your_" in gmail:
        print(f"[DEMO] {manzil} -> tasdiqlash kodi: {kod}")
        return False

    msg = MIMEText(
        f"Xorazm Pedagogika Texnikumi Kutubxonasi\n\n"
        f"Sizning tasdiqlash kodingiz: {kod}\n\n"
        f"Agar bu siz bo'lsangiz, kodni kiriting. Aks holda e'tibor bermang."
    )
    msg["Subject"] = "Kutubxona - Tasdiqlash kodi"
    msg["From"] = gmail
    msg["To"] = manzil

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail, parol)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email yuborishda xato: {e}")
        print(f"[DEMO REJIM] {manzil} -> tasdiqlash kodi: {kod}")
        return False


def joriy_foydalanuvchi():
    return session.get("foydalanuvchi")


ADMIN_LOGIN = "Tohir"
ADMIN_PAROL = "Tohir_1993"


def admin_mi():
    f = joriy_foydalanuvchi()
    return f and f.get("email") == "admin"


HTML = """
<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<title>Xorazm Pedagogika Texnikumi Kutubxonasi</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #1a3a6e, #2c5aa0); margin: 0; min-height: 100vh; }
  .header { background: rgba(0,0,0,0.3); padding: 15px; color: white; display: flex; justify-content: space-between; align-items: center; }
  .header h1 { margin: 0; font-size: 22px; }
  .header-right a { color: white; margin-left: 15px; text-decoration: none; }
  .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
  .nav { background: #fff; padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center; }
  .nav a { color: #1a3a6e; margin: 0 12px; text-decoration: none; font-weight: bold; }
  .flash { padding: 12px; border-radius: 6px; margin: 10px auto; max-width: 600px; text-align: center; }
  .flash-muvaffaqiyat { background: #d4edda; color: #155724; }
  .flash-xato { background: #f8d7da; color: #721c24; }
  .auth-form { background: #fff; padding: 30px; border-radius: 10px; max-width: 450px; margin: 30px auto; }
  .auth-form h2 { text-align: center; color: #1a3a6e; margin-top: 0; }
  .auth-form input, .auth-form select { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 6px; }
  .auth-form button { width: 100%; background: #1a3a6e; color: white; padding: 12px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }
  .auth-link { text-align: center; margin-top: 15px; }
  .auth-link a { color: #1a3a6e; }
  .bolim-sarlavha { color: white; background: rgba(0,0,0,0.3); padding: 12px; border-radius: 10px; margin: 20px 0 10px; }
  .kitoblar { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; }
  .karta { background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.15); transition: transform 0.2s; }
  .karta:hover { transform: translateY(-5px); }
  .muqova { width: 100%; height: 280px; background: linear-gradient(135deg, #1a3a6e, #2c5aa0); display: flex; align-items: center; justify-content: center; color: white; font-size: 48px; font-weight: bold; }
  .muqova img { width: 100%; height: 280px; object-fit: cover; }
  .karta-tana { padding: 15px; }
  .karta-tana h3 { margin: 0 0 8px; color: #1a3a6e; font-size: 16px; }
  .karta-tana p { margin: 4px 0; color: #666; font-size: 14px; }
  .karta-tana .yuklagan { font-size: 12px; color: #999; font-style: italic; }
  .tugmalar { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; }
  .btn { flex: 1; min-width: 70px; padding: 7px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; text-align: center; font-size: 12px; color: white; }
  .btn-ochish { background: #1a3a6e; }
  .btn-yuklash { background: #28a745; }
  .btn-tahrirlash { background: #ffc107; color: #333; }
  .btn-ochirish { background: #dc3545; }
  form { background: #fff; padding: 20px; border-radius: 10px; margin: 20px 0; }
  form input, form select { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 6px; }
  form button { background: #1a3a6e; color: white; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; }
  .qidiruv-form { display: flex; gap: 10px; }
  .qidiruv-form input { flex: 1; }
  .reader { background: #fff; padding: 20px; border-radius: 10px; text-align: center; }
  .reader iframe { width: 100%; height: 600px; border: none; border-radius: 8px; }
</style>
</head>
<body>
<div class="header">
  <h1>Xorazm Pedagogika Texnikumi — Kutubxona</h1>
  <div class="header-right">
    {% if foydalanuvchi %}
      <span>Salom, <b>{{ foydalanuvchi.ism }}</b>!</span>
      <a href="{{ url_for('chiqish') }}">Chiqish</a>
    {% else %}
      <a href="{{ url_for('kirish') }}">Kirish</a>
      <a href="{{ url_for('royxat') }}">Ro'yxatdan o'tish</a>
    {% endif %}
  </div>
</div>
<div class="container">

  {% with xabarlar = get_flashed_messages(with_categories=true) %}
    {% for tur, xabar in xabarlar %}
      <div class="flash flash-{{ tur }}">{{ xabar }}</div>
    {% endfor %}
  {% endwith %}

  {% if sahifa == 'bosh' %}
    <div class="nav">
      <a href="{{ url_for('bosh_sahifa') }}">Bosh sahifa</a>
      <a href="{{ url_for('qidirish') }}">Qidirish</a>
      {% if foydalanuvchi %}
        <a href="{{ url_for('qoshish') }}">Kitob qo'shish</a>
      {% endif %}
    </div>

    {% for bolim in bolimlar %}
      <div class="bolim-sarlavha">
        <h2 style="margin:0">{{ bolim }} <small>({{ malumot[bolim]|length }} ta)</small></h2>
      </div>
      {% if malumot[bolim] %}
      <div class="kitoblar">
        {% for kitob in malumot[bolim] %}
        <div class="karta">
          <div class="muqova">
            {% if kitob.muqova %}
              <img src="{{ url_for('static', filename='covers/' + kitob.muqova) }}" alt="">
            {% else %}
              {{ kitob.nomi[0]|upper }}
            {% endif %}
          </div>
          <div class="karta-tana">
            <h3>{{ kitob.nomi }}</h3>
            <p>{{ kitob.muallif }}</p>
            <p>{{ kitob.yili }}</p>
            <p class="yuklagan">Yukladi: {{ kitob.tomonidan or 'Tizim' }}</p>
            <div class="tugmalar">
              {% if kitob.fayl %}
                <a class="btn btn-ochish" href="{{ url_for('ochish', bolim=bolim, idx=loop.index0) }}">O'qish</a>
                <a class="btn btn-yuklash" href="{{ url_for('static', filename='files/' + kitob.fayl) }}" download>Yuklab</a>
              {% endif %}
              {% if foydalanuvchi and (kitob.tomonidan == foydalanuvchi.email or foydalanuvchi.rol == 'admin') %}
                <a class="btn btn-tahrirlash" href="{{ url_for('tahrirlash', bolim=bolim, idx=loop.index0) }}">Tahrir</a>
                <a class="btn btn-ochirish" href="{{ url_for('ochirish', bolim=bolim, idx=loop.index0) }}" onclick="return confirm('O\\'chirilsinmi?')">O'chirish</a>
              {% endif %}
            </div>
          </div>
        </div>
        {% endfor %}
      </div>
      {% endif %}
    {% endfor %}

  {% elif sahifa == 'qidirish' %}
    <div class="nav"><a href="{{ url_for('bosh_sahifa') }}">Bosh sahifa</a></div>
    <form class="qidiruv-form" method="get">
      <input type="text" name="so_rov" placeholder="Kitob yoki muallif izlash..." value="{{ so_rov or '' }}">
      <button type="submit">Qidirish</button>
    </form>
    {% if natija %}
    <div class="kitoblar" style="margin-top:20px">
      {% for item in natija %}
      <div class="karta">
        <div class="muqova">
          {% if item.kitob.muqova %}
            <img src="{{ url_for('static', filename='covers/' + item.kitob.muqova) }}" alt="">
          {% else %}
            {{ item.kitob.nomi[0]|upper }}
          {% endif %}
        </div>
        <div class="karta-tana">
          <small style="color:#1a3a6e">{{ item.bolim }}</small>
          <h3>{{ item.kitob.nomi }}</h3>
          <p>{{ item.kitob.muallif }} ({{ item.kitob.yili }})</p>
        </div>
      </div>
      {% endfor %}
    </div>
    {% elif so_rov %}
    <p style="color:white; text-align:center; margin-top:20px">Hech narsa topilmadi.</p>
    {% endif %}

  {% elif sahifa == 'qoshish' %}
    <div class="nav"><a href="{{ url_for('bosh_sahifa') }}">Bosh sahifa</a></div>
    <form method="post" enctype="multipart/form-data">
      <h2>Yangi kitob qo'shish</h2>
      <label>Bo'lim:</label>
      <select name="bolim">
        {% for bolim in bolimlar %}<option value="{{ bolim }}">{{ bolim }}</option>{% endfor %}
      </select>
      <label>Kitob nomi:</label>
      <input type="text" name="nomi" required>
      <label>Muallif:</label>
      <input type="text" name="muallif" required>
      <label>Yili:</label>
      <input type="text" name="yili" required>
      <label>Muqova rasmi:</label>
      <input type="file" name="muqova" accept="image/*">
      <label>Kitob fayli (PDF):</label>
      <input type="file" name="fayl" accept=".pdf">
      <button type="submit">Saqlash</button>
    </form>

  {% elif sahifa == 'tahrirlash' %}
    <div class="nav"><a href="{{ url_for('bosh_sahifa') }}">Bosh sahifa</a></div>
    <form method="post" enctype="multipart/form-data">
      <h2>Kitobni tahrirlash</h2>
      <label>Nomi:</label>
      <input type="text" name="nomi" value="{{ kitob.nomi }}" required>
      <label>Muallif:</label>
      <input type="text" name="muallif" value="{{ kitob.muallif }}" required>
      <label>Yili:</label>
      <input type="text" name="yili" value="{{ kitob.yili }}" required>
      <label>Yangi muqova (ixtiyoriy):</label>
      <input type="file" name="muqova" accept="image/*">
      <label>Yangi PDF (ixtiyoriy):</label>
      <input type="file" name="fayl" accept=".pdf">
      <button type="submit">Saqlash</button>
    </form>

  {% elif sahifa == 'ochish' %}
    <div class="nav"><a href="{{ url_for('bosh_sahifa') }}">Bosh sahifa</a></div>
    <div class="reader">
      <h2>{{ kitob.nomi }} — {{ kitob.muallif }}</h2>
      <iframe src="{{ url_for('static', filename='files/' + kitob.fayl) }}"></iframe>
      <p style="margin-top:15px">
        <a class="btn btn-yuklash" href="{{ url_for('static', filename='files/' + kitob.fayl) }}" download style="display:inline-block; width:auto; padding:12px 25px">Yuklab olish</a>
      </p>
    </div>

  {% elif sahifa == 'kirish' %}
    <form class="auth-form" method="post">
      <h2>Tizimga kirish</h2>
      <input type="email" name="email" placeholder="Email" required>
      <input type="password" name="parol" placeholder="Parol" required>
      <button type="submit">Kirish</button>
      <div class="auth-link">Akkaunt yo'qmi? <a href="{{ url_for('royxat') }}">Ro'yxatdan o'tish</a></div>
    </form>

  {% elif sahifa == 'royxat' %}
    <form class="auth-form" method="post">
      <h2>Ro'yxatdan o'tish</h2>
      <input type="text" name="ism" placeholder="Ism" required>
      <input type="text" name="familiya" placeholder="Familiya" required>
      <input type="email" name="email" placeholder="Email" required>
      <input type="password" name="parol" placeholder="Parol (kamida 6 ta)" minlength="6" required>
      <button type="submit">Ro'yxatdan o'tish</button>
      <div class="auth-link">Akkauntingiz bormi? <a href="{{ url_for('kirish') }}">Kirish</a></div>
    </form>

  {% elif sahifa == 'tasdiqlash' %}
    <form class="auth-form" method="post">
      <h2>Email tasdiqlash</h2>
      <p style="text-align:center">{{ email }} manziliga yuborilgan 6 xonali kodni kiriting</p>
      <input type="text" name="kod" placeholder="123456" maxlength="6" required style="text-align:center; font-size:20px; letter-spacing:5px">
      <button type="submit">Tasdiqlash</button>
      {% if joriy_kod %}
      <div style="background:#fff3cd; padding:10px; border-radius:6px; margin-top:15px; text-align:center; font-size:14px">
        <b>Test rejim:</b> Sizning kodingiz: <span style="font-size:18px; letter-spacing:3px; color:#1a3a6e">{{ joriy_kod }}</span>
      </div>
      {% endif %}
    </form>
  {% endif %}
</div>
</body>
</html>
"""


@app.route("/")
def bosh_sahifa():
    return render_template_string(HTML, sahifa="bosh", bolimlar=BO_LIMLAR,
                                   malumot=kitoblar_yuklash(), foydalanuvchi=joriy_foydalanuvchi())


@app.route("/qidirish")
def qidirish():
    so_rov = request.args.get("so_rov", "").strip().lower()
    natija = []
    if so_rov:
        for bolim, kitoblar in kitoblar_yuklash().items():
            for kitob in kitoblar:
                if so_rov in kitob["nomi"].lower() or so_rov in kitob["muallif"].lower():
                    natija.append({"bolim": bolim, "kitob": kitob})
    return render_template_string(HTML, sahifa="qidirish", bolimlar=BO_LIMLAR,
                                   so_rov=so_rov, natija=natija, foydalanuvchi=joriy_foydalanuvchi())


@app.route("/royxat", methods=["GET", "POST"])
def royxat():
    if request.method == "POST":
        f = foydalanuvchilar_yuklash()
        email = request.form["email"].lower().strip()
        ism = request.form["ism"]
        familiya = request.form["familiya"]

        eski_bor = email in f["faollar"] or email in f["tasdiqlanmaganlar"]
        if eski_bor:
            f["faollar"].pop(email, None)
            f["tasdiqlanmaganlar"].pop(email, None)

        kod = kod_yaratish()
        f["tasdiqlanmaganlar"][email] = {
            "ism": ism,
            "familiya": familiya,
            "parol": generate_password_hash(request.form["parol"]),
            "kod": kod,
        }
        foydalanuvchilar_saqlash(f)
        yuborildi = email_yuborish(email, kod)
        session["tasdiqlash_email"] = email
        if eski_bor:
            flash("Eski akkaunt o'chirildi. Yangi tasdiqlash kodi yuborildi.", "muvaffaqiyat")
        elif not yuborildi:
            flash("Email yuborilmadi — kod konsolda ko'rinadi.", "xato")
        return redirect(url_for("tasdiqlash"))
    return render_template_string(HTML, sahifa="royxat", foydalanuvchi=joriy_foydalanuvchi())


@app.route("/tasdiqlash", methods=["GET", "POST"])
def tasdiqlash():
    email = session.get("tasdiqlash_email")
    if not email:
        return redirect(url_for("royxat"))
    f = foydalanuvchilar_yuklash()
    joriy_kod = f["tasdiqlanmaganlar"].get(email, {}).get("kod", "")
    if request.method == "POST":
        if email in f["tasdiqlanmaganlar"]:
            kiritilgan = request.form["kod"].strip()
            if f["tasdiqlanmaganlar"][email]["kod"] == kiritilgan:
                malumot = f["tasdiqlanmaganlar"].pop(email)
                f["faollar"][email] = malumot
                foydalanuvchilar_saqlash(f)
                session["foydalanuvchi"] = {"ism": malumot["ism"], "email": email}
                session.pop("tasdiqlash_email", None)
                flash("Muvaffaqiyatli ro'yxatdan o'tdingiz!", "muvaffaqiyat")
                return redirect(url_for("bosh_sahifa"))
            else:
                flash("Kod noto'g'ri", "xato")
    return render_template_string(HTML, sahifa="tasdiqlash", email=email,
                                   joriy_kod=joriy_kod, foydalanuvchi=joriy_foydalanuvchi())


@app.route("/kirish", methods=["GET", "POST"])
def kirish():
    if request.method == "POST":
        email = request.form["email"].strip()
        parol = request.form["parol"]

        if email == ADMIN_LOGIN and parol == ADMIN_PAROL:
            session["foydalanuvchi"] = {"ism": "Admin (Tohir)", "email": "admin", "rol": "admin"}
            flash("Xush kelibsiz, Admin!", "muvaffaqiyat")
            return redirect(url_for("bosh_sahifa"))

        email_l = email.lower()
        f = foydalanuvchilar_yuklash()
        user = f["faollar"].get(email_l)
        if user and check_password_hash(user["parol"], parol):
            session["foydalanuvchi"] = {"ism": user["ism"], "email": email_l, "rol": "user"}
            flash(f"Xush kelibsiz, {user['ism']}!", "muvaffaqiyat")
            return redirect(url_for("bosh_sahifa"))
        flash("Email yoki parol noto'g'ri", "xato")
    return render_template_string(HTML, sahifa="kirish", foydalanuvchi=joriy_foydalanuvchi())


@app.route("/chiqish")
def chiqish():
    session.clear()
    return redirect(url_for("bosh_sahifa"))


@app.route("/qoshish", methods=["GET", "POST"])
def qoshish():
    if not joriy_foydalanuvchi():
        flash("Kitob qo'shish uchun tizimga kiring", "xato")
        return redirect(url_for("kirish"))
    if request.method == "POST":
        m = kitoblar_yuklash()
        muqova_nom = ""
        fayl_nom = ""
        if "muqova" in request.files:
            f = request.files["muqova"]
            if f.filename:
                muqova_nom = secure_filename(f.filename)
                f.save(os.path.join(app.config["COVER_FOLDER"], muqova_nom))
        if "fayl" in request.files:
            f = request.files["fayl"]
            if f.filename:
                fayl_nom = secure_filename(f.filename)
                f.save(os.path.join(app.config["UPLOAD_FOLDER"], fayl_nom))
        m[request.form["bolim"]].append({
            "nomi": request.form["nomi"],
            "muallif": request.form["muallif"],
            "yili": request.form["yili"],
            "muqova": muqova_nom,
            "fayl": fayl_nom,
            "tomonidan": joriy_foydalanuvchi()["email"],
        })
        kitoblar_saqlash(m)
        flash("Kitob qo'shildi!", "muvaffaqiyat")
        return redirect(url_for("bosh_sahifa"))
    return render_template_string(HTML, sahifa="qoshish", bolimlar=BO_LIMLAR, foydalanuvchi=joriy_foydalanuvchi())


@app.route("/tahrirlash/<bolim>/<int:idx>", methods=["GET", "POST"])
def tahrirlash(bolim, idx):
    user = joriy_foydalanuvchi()
    if not user:
        return redirect(url_for("kirish"))
    m = kitoblar_yuklash()
    kitob = m[bolim][idx]
    if not admin_mi() and kitob.get("tomonidan") != user["email"]:
        flash("Faqat o'zingiz yuklagan kitobni tahrirlashingiz mumkin", "xato")
        return redirect(url_for("bosh_sahifa"))
    if request.method == "POST":
        m[bolim][idx]["nomi"] = request.form["nomi"]
        m[bolim][idx]["muallif"] = request.form["muallif"]
        m[bolim][idx]["yili"] = request.form["yili"]
        if "muqova" in request.files:
            f = request.files["muqova"]
            if f.filename:
                nom = secure_filename(f.filename)
                f.save(os.path.join(app.config["COVER_FOLDER"], nom))
                m[bolim][idx]["muqova"] = nom
        if "fayl" in request.files:
            f = request.files["fayl"]
            if f.filename:
                nom = secure_filename(f.filename)
                f.save(os.path.join(app.config["UPLOAD_FOLDER"], nom))
                m[bolim][idx]["fayl"] = nom
        kitoblar_saqlash(m)
        return redirect(url_for("bosh_sahifa"))
    return render_template_string(HTML, sahifa="tahrirlash", bolimlar=BO_LIMLAR,
                                   kitob=kitob, foydalanuvchi=user)


@app.route("/ochirish/<bolim>/<int:idx>")
def ochirish(bolim, idx):
    user = joriy_foydalanuvchi()
    if not user:
        return redirect(url_for("kirish"))
    m = kitoblar_yuklash()
    kitob = m[bolim][idx]
    if not admin_mi() and kitob.get("tomonidan") != user["email"]:
        flash("Faqat o'zingiz yuklagan kitobni o'chirishingiz mumkin", "xato")
        return redirect(url_for("bosh_sahifa"))
    m[bolim].pop(idx)
    kitoblar_saqlash(m)
    return redirect(url_for("bosh_sahifa"))


@app.route("/ochish/<bolim>/<int:idx>")
def ochish(bolim, idx):
    kitob = kitoblar_yuklash()[bolim][idx]
    return render_template_string(HTML, sahifa="ochish", bolimlar=BO_LIMLAR,
                                   kitob=kitob, foydalanuvchi=joriy_foydalanuvchi())


if __name__ == "__main__":
    app.run(debug=True)