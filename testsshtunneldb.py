from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sshtunnel import SSHTunnelForwarder

app = Flask(__name__)

# Konfigurasi SSH tunnel
ssh_server = SSHTunnelForwarder(
    ('billing.tachyon.net.id', 22),  # Alamat server SSH dan port
    ssh_username='ngadimins2015',
    ssh_password='Ganteng@2015',  # Atau gunakan ssh_pkey untuk kunci privat
    remote_bind_address=('127.0.0.1', 3306),  # Alamat dan port MySQL di server remote
    local_bind_address=('0.0.0.0', 10000)  # Alamat dan port lokal untuk mengakses MySQL
)

ssh_server.start()

# Konfigurasi Flask-SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql://billing_idf:!B1ll1n6_1dF@127.0.0.1:{ssh_server.local_bind_port}/billing_idf"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route('/')
def index():
    # Contoh query
    result = db.engine.execute("SELECT 1")
    return f"Query result: {result.fetchone()}"

if __name__ == "__main__":
    try:
        app.run(debug=True)
    finally:
        ssh_server.stop()
