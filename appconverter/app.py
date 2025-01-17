from flask import Blueprint
from flask_restful import Api
from flask_cors import CORS

appconverter_api = Blueprint('appconverter_api', __name__)
CORS(appconverter_api, supports_credentials=True, resources=r'*', origins='*', methods=['GET','POST','PUT','DELETE'])
api = Api(appconverter_api)

from .converter import ConverterCsvApi

api.add_resource(ConverterCsvApi, '')

def init_docs(docs):
    docs.register(ConverterCsvApi, blueprint='appconverter_api')