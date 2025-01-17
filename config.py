import os

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
from sshtunnel import SSHTunnelForwarder
from sqlalchemy import event

# Konfigurasi SSH tunnel
ssh_server = SSHTunnelForwarder(
    ('billing.tachyon.net.id', 22),  # Alamat server SSH dan port
    ssh_username='ngadimins2015',
    ssh_password='Ganteng@2015',  # Atau gunakan ssh_pkey untuk kunci privat
    remote_bind_address=('127.0.0.1', 3306),  # Alamat dan port MySQL di server remote
    local_bind_address=('0.0.0.0', 10000)  # Alamat dan port lokal untuk mengakses MySQL
)

ssh_server.start()

class ApplicationConfig:
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"
    SECRET_KEY = 'd87cfdc4a4e90feea40b28070b5411e8'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    #SQLALCHEMY_DATABASE_URI = f"mysql://billing_idf:!B1ll1n6_1dF@127.0.0.1:{ssh_server.local_bind_port}/billing_idf"
    SQLALCHEMY_DATABASE_URI = "sqlite:///{}".format(os.path.join(os.path.dirname(__file__), "dblocal.db"))
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True, 'pool_recycle':5}
    SQLALCHEMY_POOL_SIZE = 1000
    SQLALCHEMY_MAX_OVERFLOW = -1
    SQLALCHEMY_POOL_TIMEOUT = 300
    SQLALCHEMY_BINDS = {
        'dbrudi': f"mysql://billing_idf:!B1ll1n6_1dF@127.0.0.1:{ssh_server.local_bind_port}/billing_idf?charset=latin1"
    }
    APISPEC_SPEC = APISpec(
        title='ERPRudi',
        version='0.0.1',
        plugins=[MarshmallowPlugin()],
        openapi_version='2.0.0'
    )
    #api_key_scheme = {"type": "apiKey", "in": "header", "name": "Authorization"}
    #APISPEC_SPEC.components.security_scheme("ApiKeyAuth", api_key_scheme)
    APISPEC_SWAGGER_URL = '/swagger/'
    APISPEC_SWAGGER_UI_URL = '/swagger-ui/'
    