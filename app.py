from flask import Flask, jsonify, request, has_request_context, render_template
from config import ApplicationConfig
from flask_apispec.extension import FlaskApiSpec
from flask_cors import CORS
from flask_session import Session
from logging.handlers import TimedRotatingFileHandler
import logging
import os
import time

app = Flask(__name__)
CORS(app, supports_credentials=True, resources=r'*', origins="*", methods=['GET','POST','PUT','DELETE'])
app.config.from_object(ApplicationConfig)

# Set up logging
log_dir = 'log'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

class RequestFormatter(logging.Formatter):
    def format(self, record):
        try:
            if has_request_context():
                record.url = request.url
                record.remote_addr = request.remote_addr
                record.method = request.method
                record.status = request.status_code
                record.response_time = request.response_time
            else:
                raise Exception
        except:
                record.url = None
                record.remote_addr = None
                record.method = None
                record.status = None
                record.response_time = None
        return super().format(record)
    
access_log_handler = TimedRotatingFileHandler(
    filename=os.path.join(log_dir, 'access.log'),
    when='midnight',
    interval=1,
    backupCount=7,
    encoding='utf-8'
)

error_log_handler = TimedRotatingFileHandler(
    filename=os.path.join(log_dir, 'error.log'),
    when='midnight',
    interval=1,
    backupCount=7,
    encoding='utf-8'
)

# Define the log format
access_formatter = RequestFormatter(
    "%(asctime)s - %(remote_addr)s - %(method)s - %(url)s - %(status)s - %(response_time)s ms"
)
error_formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s in %(module)s: %(message)s %(msecs)d"
)

access_log_handler.setFormatter(access_formatter)
error_log_handler.setFormatter(error_formatter)

app.logger.addHandler(access_log_handler)
app.logger.addHandler(error_log_handler)

access_log_handler.setLevel(logging.INFO)
error_log_handler.setLevel(logging.DEBUG)

app.logger.setLevel(logging.DEBUG)

@app.before_request
def start_timer():
    request.start_time = time.time()
    if request.method in ['POST', 'PUT', 'DELETE']:  # Only log body for write operations
        app.logger.info(
            "Request: %s %s %s\nHeaders: %s\nBody: %s",
            request.method,
            request.url,
            request.content_type,
            dict(request.headers),
            request.get_data(as_text=True),  # Get raw body as text
        )
    else:
        app.logger.info(
            "Request: %s %s\nHeaders: %s",
            request.method,
            request.url,
            dict(request.headers),
        )

@app.after_request
def log_request(response):
    response_time = (time.time() - request.start_time) * 1000  # Convert to milliseconds
    request.status_code = response.status_code
    request.response_time = f"{response_time:.2f}"
    if response.content_type == 'application/json':
        app.logger.info(
            "Response: %s - %s - %s - %s - %s - %s ms \nHeaders: %s\nBody: %s",
            request.remote_addr,
            request.method,
            request.url,
            response.status_code,
            response.content_type,
            request.response_time,
            dict(response.headers),
            response.get_data(as_text=True)
        )
    else:
        app.logger.info(
            "Response: %s - %s - %s - %s - %s - %s ms \nHeaders: %s",
            request.remote_addr,
            request.method,
            request.url,
            response.status_code,
            response.content_type,
            request.response_time,
            dict(response.headers)
        )
    return response


from config import db
from appconverter.models import init_db as init_db_local
#scheduler.init_app(app)
db.init_app(app)
init_db_local(app)

from werkzeug.exceptions import HTTPException
@app.errorhandler(Exception)
def handle_error(e):
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
    app.logger.error(str(e))
    return jsonify(error=str(e)), code
Session(app)

@app.route('/')
def index():
    return render_template('index.html')

with app.app_context():
    docs = FlaskApiSpec(app)

    #erp parsing
    from appconverter.app import init_docs as init_docs_appconverter, appconverter_api
    app.register_blueprint(appconverter_api, url_prefix='/converter')
    init_docs_appconverter(docs)

    #app rudi
    from apprudi.app import init_docs as init_docs_apprudi, apprudi_api
    app.register_blueprint(apprudi_api, url_prefix='/apprudi')
    init_docs_apprudi(docs)

if __name__ == "__main__":
    app.run('0.0.0.0', port=5000,debug=True)