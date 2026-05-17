from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "kunci_rahasia_perpustakaan_final_banget"

# --- CONFIG DATABASE ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/db_perpustakaan'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELS ---
class Petugas(db.Model):
    id_petugas = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(255))

class Buku(db.Model):
    isbn = db.Column(db.String(20), primary_key=True)
    judul = db.Column(db.String(255))
    penulis = db.Column(db.String(100))
    stok = db.Column(db.Integer, default=0)

class Anggota(db.Model):
    nim = db.Column(db.String(15), primary_key=True)
    nama = db.Column(db.String(100))
    prodi = db.Column(db.String(50))

class Peminjaman(db.Model):
    id_pinjam = db.Column(db.Integer, primary_key=True)
    id_anggota = db.Column(db.String(15))
    isbn = db.Column(db.String(20))
    tgl_pinjam = db.Column(db.DateTime, default=datetime.now)
    tgl_tenggat = db.Column(db.DateTime)
    tgl_kembali = db.Column(db.DateTime, nullable=True)
    denda = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='Dipinjam')

    def __init__(self, **kwargs):
        super(Peminjaman, self).__init__(**kwargs)
        if not self.tgl_tenggat:
            self.tgl_tenggat = datetime.now() + timedelta(days=7)

with app.app_context():
    db.create_all()

# --- CSS STYLING ---
HEAD = """
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
<style>
    body { background: #f4f7f6; font-family: 'Segoe UI', sans-serif; }
    .sidebar { min-width: 250px; background: #1a237e; color: white; min-height: 100vh; padding: 20px; position: sticky; top: 0; }
    .sidebar a { color: #cfd8dc; text-decoration: none; display: block; padding: 10px; border-radius: 5px; margin-bottom: 5px; }
    .sidebar a:hover, .sidebar a.active { background: #283593; color: white; }
    .card { border: none; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .table-container { background: white; border-radius: 10px; overflow: hidden; border: 1px solid #dee2e6; }
</style>
"""

# --- ROUTES ---

@app.route('/')
def katalog():
    buku = Buku.query.all()
    cards = "".join([f'''
        <div class="col-md-3 mb-4">
            <div class="card p-3 h-100 text-center">
                <i class="bi bi-book fs-1 text-primary mb-2"></i>
                <h6 class="fw-bold">{b.judul}</h6>
                <p class="text-muted small">ISBN: {b.isbn}</p>
                <div class="badge {'bg-success' if b.stok > 0 else 'bg-danger'}">Stok: {b.stok}</div>
            </div>
        </div>
    ''' for b in buku])
    return render_template_string(f"{HEAD}<div class='container mt-5'> <div class='d-flex justify-content-between mb-4'><h2>📚 Katalog Perpustakaan</h2><a href='/login' class='btn btn-outline-primary'>Portal Admin</a></div> <div class='row'>{cards}</div></div>")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Petugas.query.filter_by(username=request.form['user'], password=request.form['pass']).first()
        if user:
            session['user'] = user.username
            return redirect(url_for('admin'))
    return render_template_string(f"{HEAD}<div class='d-flex justify-content-center align-items-center' style='height: 100vh;'><div class='card p-4 shadow' style='width: 350px;'><h4 class='text-center mb-4'>Login Petugas</h4><form method='POST'><input name='user' class='form-control mb-3' placeholder='Username' required><input type='password' name='pass' class='form-control mb-4' placeholder='Password' required><button class='btn btn-primary w-100'>Login</button></form><div class='text-center mt-3 small'><a href='/register'>Daftar Petugas Baru</a></div></div></div>")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        db.session.add(Petugas(username=request.form['user'], password=request.form['pass']))
        db.session.commit()
        return redirect(url_for('login'))
    return render_template_string(f"{HEAD}<div class='d-flex justify-content-center align-items-center' style='height: 100vh;'><div class='card p-4 shadow' style='width: 350px;'><h4 class='text-center mb-4'>Register Petugas</h4><form method='POST'><input name='user' class='form-control mb-3' placeholder='Username' required><input type='password' name='pass' class='form-control mb-4' placeholder='Password' required><button class='btn btn-success w-100 text-white'>Daftar</button></form></div></div>")

@app.route('/admin')
def admin():
    if 'user' not in session: return redirect(url_for('login'))
    buku, mhs, pinjam = Buku.query.all(), Anggota.query.all(), Peminjaman.query.order_by(Peminjaman.id_pinjam.desc()).all()
    
    rows_b = "".join([f"<tr><td>{b.isbn}</td><td>{b.judul}</td><td>{b.stok}</td><td><a href='/hapus_buku/{b.isbn}' class='text-danger'><i class='bi bi-trash'></i></a></td></tr>" for b in buku])
    rows_m = "".join([f"<tr><td>{a.nim}</td><td>{a.nama}</td><td>{a.prodi}</td><td><a href='/hapus_mhs/{a.nim}' class='text-danger'><i class='bi bi-person-x'></i></a></td></tr>" for a in mhs])
    
    rows_p = ""
    for p in pinjam:
        tgl_p = p.tgl_pinjam.strftime('%d/%m/%Y')
        tgl_t = p.tgl_tenggat.strftime('%d/%m/%Y')
        tgl_k = p.tgl_kembali.strftime('%d/%m/%Y') if p.tgl_kembali else "-"
        status_color = "bg-warning text-dark" if p.status == 'Dipinjam' else "bg-success"
        btn = f'<a href="/kembali/{p.id_pinjam}" class="btn btn-sm btn-success">Kembalikan</a>' if p.status == 'Dipinjam' else '-'
        
        rows_p += f"<tr><td>{p.id_anggota}</td><td>{tgl_p}</td><td>{tgl_t}</td><td>{tgl_k}</td><td>Rp {p.denda:,}</td><td><span class='badge {status_color}'>{p.status}</span></td><td>{btn}</td></tr>"

    return render_template_string(f"""
    {HEAD}
    <div class="d-flex">
        <div class="sidebar">
            <h4 class="mb-5 text-center">SIPUS ADMIN</h4>
            <a href="/admin" class="active"><i class="bi bi-speedometer2"></i> DASHBOARD</a>
            <a href="/"><i class="bi bi-house"></i> Lihat Katalog</a>
            <a href="/logout" class="text-danger mt-5"><i class="bi bi-power"></i> LOGOUT</a>
        </div>
        <div class="p-4 w-100">
            <h3 class="mb-4">Manajemen Sirkulasi</h3>
            <div class="row g-3 mb-4">
                <div class="col-md-4"><div class="card p-3"><h6>Buku Baru</h6><form action="/tambah_buku" method="POST"><input name="isbn" placeholder="ISBN" class="form-control mb-2" required><input name="judul" placeholder="Judul" class="form-control mb-2" required><input name="penulis" placeholder="Penulis" class="form-control mb-2" required><input name="stok" type="number" placeholder="Stok" class="form-control mb-2" required><button class="btn btn-primary btn-sm w-100">Simpan Buku</button></form></div></div>
                <div class="col-md-4"><div class="card p-3"><h6>Tambah Mahasiswa</h6><form action="/tambah_mhs" method="POST"><input name="nim" placeholder="NIM" class="form-control mb-2" required><input name="nama" placeholder="Nama" class="form-control mb-2" required><input name="prodi" placeholder="Prodi" class="form-control mb-2" required><button class="btn btn-success btn-sm w-100 text-white">Tambah Anggota</button></form></div></div>
                <div class="col-md-4"><div class="card p-3"><h6>Transaksi Pinjam</h6><form action="/pinjam" method="POST"><input name="nim" placeholder="NIM Mahasiswa" class="form-control mb-2" required><input name="isbn" placeholder="ISBN Buku" class="form-control mb-2" required><button class="btn btn-warning btn-sm w-100">Catat Peminjaman</button></form></div></div>
            </div>

            <h5 class="mt-4">Riwayat Transaksi</h5>
            <div class="table-container shadow-sm mb-4"><table class="table align-middle mb-0"><thead><tr><th>NIM</th><th>Tgl.Pinjam</th><th>Tgl.Tenggat</th><th>Tgl.Kembali</th><th>Denda</th><th>Status</th><th>Aksi</th></tr></thead><tbody>{rows_p}</tbody></table></div>

            <div class="row">
                <div class="col-md-6"><h5>Daftar Mahasiswa</h5><div class="table-container shadow-sm"><table class="table align-middle"><thead><tr><th>NIM</th><th>Nama</th><th>Prodi</th><th>Aksi</th></tr></thead><tbody>{rows_m}</tbody></table></div></div>
                <div class="col-md-6"><h5>Daftar Koleksi Buku</h5><div class="table-container shadow-sm"><table class="table align-middle"><thead><tr><th>ISBN</th><th>Judul</th><th>Stok</th><th>Aksi</th></tr></thead><tbody>{rows_b}</tbody></table></div></div>
            </div>
        </div>
    </div>
    """)

# --- LOGIKA ---

@app.route('/tambah_buku', methods=['POST'])
def tambah_buku():
    db.session.add(Buku(isbn=request.form['isbn'], judul=request.form['judul'], penulis=request.form['penulis'], stok=request.form['stok']))
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/tambah_mhs', methods=['POST'])
def tambah_mhs():
    db.session.add(Anggota(nim=request.form['nim'], nama=request.form['nama'], prodi=request.form['prodi']))
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/pinjam', methods=['POST'])
def pinjam():
    mhs = Anggota.query.get(request.form['nim'])
    buku = Buku.query.get(request.form['isbn'])
    if mhs and buku and buku.stok > 0:
        db.session.add(Peminjaman(id_anggota=mhs.nim, isbn=buku.isbn))
        buku.stok -= 1
        db.session.commit()
    return redirect(url_for('admin'))

@app.route('/kembali/<int:id_pinjam>')
def kembali(id_pinjam):
    p = Peminjaman.query.get(id_pinjam)
    if p and p.status == 'Dipinjam':
        p.tgl_kembali = datetime.now()
        p.status = 'Kembali'
        if p.tgl_kembali > p.tgl_tenggat:
            p.denda = (p.tgl_kembali - p.tgl_tenggat).days * 1000
        b = Buku.query.get(p.isbn)
        if b: b.stok += 1
        db.session.commit()
    return redirect(url_for('admin'))

@app.route('/hapus_buku/<isbn>')
def hapus_buku(isbn):
    db.session.delete(Buku.query.get(isbn))
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/hapus_mhs/<nim>')
def hapus_mhs(nim):
    db.session.delete(Anggota.query.get(nim))
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)