from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
import sqlite3, hashlib, os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'estt_tetouan_super_secret_2025')
DB = 'estt.db'

MAJORS = {
    "IA": {
        "name": "Intelligence Artificielle", "color": "#6366f1", "icon": "🤖",
        "semesters": {
            1: ["Architecture des Ordinateurs et Systemes d'Exploitation","Algorithmes et Programmation Python","Mathematiques pour l'Apprentissage Automatique 1","Reseaux et Securite Informatique","Probabilites et Statistiques pour la Science des Donnees","Langues et Techniques de Communication 1","MTU et Developpement Personnel"],
            2: ["Introduction a l'Intelligence Artificielle","Algorithmes et Structures de Donnees","Modelisation des Systemes d'Information et DB","Mathematiques pour l'Apprentissage Automatique 2","Introduction a DevOps","Langues et Techniques de Communication 2","Competences Numeriques"],
            3: ["Techniques du Web et Architectures Distribuees","Big Data et Bases de Donnees NoSQL","Science des Donnees Appliquees","Apprentissage Automatique","MLOps: CI/CD pour l'Apprentissage Automatique","Python Avance","Apprentissage Profond et Vision par Ordinateur"],
            4: ["Introduction a l'IA Embarquee","Communication et Culture de l'Entreprise","Informatique en Nuage (Cloud)","IA Generative et Agents Intelligents","Projet de Fin d'Etudes (PFE)","Stage d'Initiation et Stage Technique"]
        }
    },
    "IDD": {
        "name": "Informatique et Developpement Digital", "color": "#10b981", "icon": "💻",
        "semesters": {
            1: ["Langues et Techniques de Communication 1","Python 1 : Algorithmes et Programmation","Architecture des Ordinateurs et OS","Reseaux et Securite Informatique","Introduction aux Statistiques et Probabilites","Mathematiques pour Machine Learning","Culture Digitale"],
            2: ["Python 2 : Algorithmes et Structures de Donnees","Bases de Donnees et SGBD Relationnel","Visualisation des Donnees","Initiation a l'Intelligence Artificielle","Introduction a DevOps","Langues et Techniques de Communication 2","Programmation C/C++"],
            3: ["Gestion des Projets Data et UML","Fondamentaux du Big Data","Initiation a la Realite Virtuelle et Augmentee","Techniques Web et Architectures Distribuees","Intelligence Artificielle Avancee","Bases de Donnees Avancees","Entrepreneuriat et Innovation"],
            4: ["Cloud Computing et DevOps","Securite des Applications Web","Communication et Culture de l'Entreprise","Projet Integre Digital","Projet de Fin d'Etudes (PFE)","Stage Technique"]
        }
    },
    "CASI": {
        "name": "Cybersecurite et Audit des Systemes d'Information", "color": "#ef4444", "icon": "🔐",
        "semesters": {
            1: ["Mathematiques pour la Cybersecurite","Algorithmes et Programmation Python","Fondamentaux des Reseaux et Protocoles","Systeme de Gestion de Base de Donnees","Architecture des Ordinateurs et OS","Langues et Techniques de Communication 1","Power Skills : Methodologie"],
            2: ["Programmation C","Cryptographie Appliquee","Administration Windows Server","POO et Programmation Python","Securite des Reseaux","Langues et Techniques de Communication 2","Power Skills : Culture Digitale"],
            3: ["Tests d'Intrusion (Pentesting)","Introduction a l'Analyse de Logs","Administration Linux et Securisation","Forensics Numeriques et Investigation","Securite des Applications Web","Gestion des Risques et Conformite ISO 27001","Langues et Communication Professionnelle"],
            4: ["SOC et Gestion des Incidents de Securite","IA et Cybersecurite","Audit des Systemes d'Information","RGPD et Droit du Numerique","Projet de Fin d'Etudes (PFE)","Stage Technique"]
        }
    },
    "INSEM": {
        "name": "Industrie Navale : Systemes Electriques et Maintenance", "color": "#f59e0b", "icon": "⚓",
        "semesters": {
            1: ["Mathematiques I","Bases de l'Electricite","Physique de Base","Environnement Maritime et Architecture du Navire","Mecanique du Point et Pneumatique","Competences Numeriques pour le Monde Professionnel","Langues et Techniques de Communication I"],
            2: ["Electrotechnique","Mecanique des Fluides et Hydraulique","Mathematique II","Electronique","Conception Assistee par Ordinateur","Algorithmique et Programmation","Langues et Techniques de Communication II"],
            3: ["Systemes Electriques Navals","Maintenance Industrielle et Navale","Automatisme et Instrumentation","Propulsion Navale et Systemes Energetiques","Reseaux Electriques Embarques","Capteurs et Mesures","Communication Technique et Rapport"],
            4: ["Systemes de Securite et Regulation Maritime","Diagnostic et Depannage Electrique Naval","Gestion de Maintenance Assistee par Ordinateur (GMAO)","Qualite et Normes Maritimes","Projet de Fin d'Etudes (PFE)","Stage Technique"]
        }
    }
}

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()
def get_db():
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row; return conn
def calc_avg(cc1,cc2,tp,exam): return round(cc1*0.15+cc2*0.15+tp*0.20+exam*0.50,2)
def mention(avg):
    if avg>=16: return ("Tres Bien","success")
    if avg>=14: return ("Bien","info")
    if avg>=12: return ("Assez Bien","primary")
    if avg>=10: return ("Passable","warning")
    return ("Insuffisant","danger")

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            student_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL, email TEXT NOT NULL,
            major_code TEXT NOT NULL, semester INTEGER NOT NULL,
            bac_year INTEGER NOT NULL, bac_serie TEXT NOT NULL, bac_mention TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL, module TEXT NOT NULL,
            cc1 REAL DEFAULT 0, cc2 REAL DEFAULT 0, tp REAL DEFAULT 0,
            final_exam REAL DEFAULT 0, average REAL DEFAULT 0,
            FOREIGN KEY(student_id) REFERENCES students(id)
        );
    ''')
    if not conn.execute("SELECT id FROM users WHERE username='youssef'").fetchone():
        conn.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                     ('admin', hash_pw('9577you'), 'admin'))
    conn.commit(); conn.close()

def login_required(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        if 'user_id' not in session:
            flash('Please log in first.','danger')
            return redirect(url_for('login'))
        return f(*args,**kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        if 'user_id' not in session: return redirect(url_for('login'))
        if session.get('role')!='admin':
            flash('Admin access required.','danger')
            return redirect(url_for('my_profile'))
        return f(*args,**kwargs)
    return decorated

@app.route('/login', methods=['GET','POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard') if session['role']=='admin' else url_for('my_profile'))
    if request.method=='POST':
        username = request.form['username'].strip()
        password = hash_pw(request.form['password'])
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?",(username,password)).fetchone()
        conn.close()
        if user:
            session['user_id']    = user['id']
            session['username']   = user['username']
            session['role']       = user['role']
            session['student_id'] = user['student_id']
            return redirect(url_for('dashboard') if user['role']=='admin' else url_for('my_profile'))
        flash('Invalid username or password.','danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

@app.route('/my-profile')
@login_required
def my_profile():
    if session['role']=='admin': return redirect(url_for('dashboard'))
    sid = session.get('student_id')
    if not sid:
        return render_template('no_profile.html')
    conn = get_db()
    student = conn.execute('SELECT * FROM students WHERE id=?',(sid,)).fetchone()
    grades  = conn.execute('SELECT * FROM grades WHERE student_id=? ORDER BY id',(sid,)).fetchall()
    conn.close()
    sem_avg = round(sum(g['average'] for g in grades)/len(grades),2) if grades else 0
    m = mention(sem_avg)
    return render_template('my_profile.html', student=student, grades=grades,
                           majors=MAJORS, sem_avg=sem_avg,
                           mention_text=m[0], mention_class=m[1], mention=mention)

@app.route('/')
@admin_required
def dashboard():
    conn = get_db()
    stats = {
        'total': conn.execute('SELECT COUNT(*) FROM students').fetchone()[0],
        'ia':    conn.execute("SELECT COUNT(*) FROM students WHERE major_code='IA'").fetchone()[0],
        'idd':   conn.execute("SELECT COUNT(*) FROM students WHERE major_code='IDD'").fetchone()[0],
        'casi':  conn.execute("SELECT COUNT(*) FROM students WHERE major_code='CASI'").fetchone()[0],
        'insem': conn.execute("SELECT COUNT(*) FROM students WHERE major_code='INSEM'").fetchone()[0],
        'users': conn.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0],
    }
    top    = conn.execute('''SELECT s.id,s.full_name,s.major_code,s.semester,ROUND(AVG(g.average),2) as avg
                             FROM students s JOIN grades g ON s.id=g.student_id
                             GROUP BY s.id ORDER BY avg DESC LIMIT 5''').fetchall()
    recent = conn.execute('SELECT * FROM students ORDER BY id DESC LIMIT 5').fetchall()
    conn.close()
    return render_template('dashboard.html',stats=stats,top=top,recent=recent,majors=MAJORS,mention=mention)

@app.route('/students')
@admin_required
def students():
    search=request.args.get('q',''); major=request.args.get('major','')
    conn=get_db()
    query='SELECT s.*,u.username FROM students s LEFT JOIN users u ON u.student_id=s.id WHERE 1=1'
    params=[]
    if search:
        query+=' AND (s.full_name LIKE ? OR s.email LIKE ?)'; params+=[f'%{search}%',f'%{search}%']
    if major:
        query+=' AND s.major_code=?'; params.append(major)
    query+=' ORDER BY s.id DESC'
    sts=conn.execute(query,params).fetchall(); conn.close()
    return render_template('students.html',students=sts,majors=MAJORS,search=search,major=major)

@app.route('/student/<int:sid>')
@admin_required
def student_detail(sid):
    conn=get_db()
    student=conn.execute('SELECT * FROM students WHERE id=?',(sid,)).fetchone()
    if not student: flash('Not found.','danger'); return redirect(url_for('students'))
    grades=conn.execute('SELECT * FROM grades WHERE student_id=? ORDER BY id',(sid,)).fetchall()
    account=conn.execute("SELECT username FROM users WHERE student_id=?",(sid,)).fetchone()
    conn.close()
    sem_avg=round(sum(g['average'] for g in grades)/len(grades),2) if grades else 0
    m=mention(sem_avg)
    return render_template('student_detail.html',student=student,grades=grades,
                           majors=MAJORS,sem_avg=sem_avg,mention_text=m[0],
                           mention_class=m[1],mention=mention,account=account)

@app.route('/add', methods=['GET','POST'])
@admin_required
def add_student():
    if request.method=='POST':
        name=request.form['full_name']; email=request.form['email']
        major=request.form['major_code']; semester=int(request.form['semester'])
        bac_year=int(request.form['bac_year']); bac_ser=request.form['bac_serie']
        bac_men=request.form['bac_mention']; username=request.form['username'].strip()
        password=request.form['password']
        conn=get_db()
        if conn.execute("SELECT id FROM users WHERE username=?",(username,)).fetchone():
            flash(f'Username "{username}" already taken.','danger'); conn.close()
            return redirect(url_for('add_student'))
        cur=conn.execute('INSERT INTO students (full_name,email,major_code,semester,bac_year,bac_serie,bac_mention) VALUES (?,?,?,?,?,?,?)',
                         (name,email,major,semester,bac_year,bac_ser,bac_men))
        sid=cur.lastrowid
        conn.execute("INSERT INTO users (username,password,role,student_id) VALUES (?,?,?,?)",
                     (username,hash_pw(password),'student',sid))
        for i,mod in enumerate(MAJORS[major]['semesters'][semester]):
            cc1=float(request.form.get(f'cc1_{i}',0)); cc2=float(request.form.get(f'cc2_{i}',0))
            tp=float(request.form.get(f'tp_{i}',0)); exam=float(request.form.get(f'exam_{i}',0))
            conn.execute('INSERT INTO grades (student_id,module,cc1,cc2,tp,final_exam,average) VALUES (?,?,?,?,?,?,?)',
                         (sid,mod,cc1,cc2,tp,exam,calc_avg(cc1,cc2,tp,exam)))
        conn.commit(); conn.close()
        flash(f'Student {name} added! Login: {username}','success')
        return redirect(url_for('student_detail',sid=sid))
    return render_template('add_student.html',majors=MAJORS)

@app.route('/delete/<int:sid>', methods=['POST'])
@admin_required
def delete_student(sid):
    conn=get_db()
    conn.execute('DELETE FROM grades WHERE student_id=?',(sid,))
    conn.execute('DELETE FROM users WHERE student_id=?',(sid,))
    conn.execute('DELETE FROM students WHERE id=?',(sid,))
    conn.commit(); conn.close()
    flash('Student deleted.','success'); return redirect(url_for('students'))

@app.route('/edit_grade/<int:gid>', methods=['POST'])
@admin_required
def edit_grade(gid):
    cc1=float(request.form['cc1']); cc2=float(request.form['cc2'])
    tp=float(request.form['tp']); exam=float(request.form['final_exam'])
    avg=calc_avg(cc1,cc2,tp,exam)
    conn=get_db()
    sid=conn.execute('SELECT student_id FROM grades WHERE id=?',(gid,)).fetchone()[0]
    conn.execute('UPDATE grades SET cc1=?,cc2=?,tp=?,final_exam=?,average=? WHERE id=?',(cc1,cc2,tp,exam,avg,gid))
    conn.commit(); conn.close()
    flash('Grade updated!','success'); return redirect(url_for('student_detail',sid=sid))

@app.route('/users')
@admin_required
def manage_users():
    conn=get_db()
    users=conn.execute('''SELECT u.*,s.full_name,s.major_code FROM users u
                          LEFT JOIN students s ON u.student_id=s.id
                          ORDER BY u.role DESC,u.id''').fetchall()
    conn.close()
    return render_template('users.html',users=users,majors=MAJORS)

@app.route('/reset_password/<int:uid>', methods=['POST'])
@admin_required
def reset_password(uid):
    new_pw=request.form['new_password']
    conn=get_db()
    conn.execute("UPDATE users SET password=? WHERE id=?",(hash_pw(new_pw),uid))
    conn.commit(); conn.close()
    flash('Password reset.','success'); return redirect(url_for('manage_users'))

@app.route('/get_modules')
@login_required
def get_modules():
    major=request.args.get('major'); sem=int(request.args.get('semester',1))
    if major in MAJORS and sem in MAJORS[major]['semesters']:
        return jsonify(MAJORS[major]['semesters'][sem])
    return jsonify([])

init_db()

@app.route('/setup-admin')
def setup_admin():
    conn = get_db()
    conn.execute("UPDATE users SET username='youssef', password=? WHERE role='admin'",
                 (hash_pw('9577you'),))
    conn.commit()
    conn.close()
    return 'Admin updated! Delete this route now.'
if __name__=='__main__':
    init_db(); app.run(debug=True)
