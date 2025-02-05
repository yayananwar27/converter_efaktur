from flask import Blueprint
from flask_restful import Api
from flask_cors import CORS

apprudi_api = Blueprint('apprudi_api', __name__)
CORS(apprudi_api, supports_credentials=True, resources=r'*', origins='*', methods=['GET','POST','PUT','DELETE'])
api = Api(apprudi_api)

from apprudi.listemail import ListEmailApi

api.add_resource(ListEmailApi, '/listemail')

def init_docs(docs):
    docs.register(ListEmailApi, blueprint='apprudi_api')