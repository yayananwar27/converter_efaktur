from flask import jsonify, current_app, abort, request, send_file
from marshmallow import Schema, fields, ValidationError
from flask_restful import Resource
from flask_apispec.views import MethodResource
from flask_apispec import marshal_with, doc, use_kwargs

class RequestListEmailSchema(Schema):
    kategori = fields.String(required=True, metadata={"description":"fmi/pc24"})
    group_by = fields.String(required=False, allow_none=True, metadata={"description":"npwp/nama_npwp/alamat_npwp/nama_client"})
    mode_test = fields.Boolean(required=False, allow_none=True, metadata={"description":"True/False"})

from .models import TblCustomer2015Model, TblKategoriCustomerModel, TblTemplateInvoiceModel

class ListEmailApi(MethodResource, Resource):
    @doc(description='List Email by PT', tags=['List Email'])
    @use_kwargs(RequestListEmailSchema, location=('json'))
    def post(self, **kwargs):
        ptnya = kwargs['kategori']
        list_kategori = [
            {'pt':'fmi','invoice':'file_invoice_html_fmi.tpl'},
            {'pt':'pc24','invoice':'file_invoice_html.tpl '}
            ]
        
        list_email = []

        if 'mode_test' in kwargs:
            if kwargs['mode_test']:
                data = [
                    {
                        "alamat": "Rumah Yayan",
                        "email": [
                            "yayan@tachyon.net.id",
                            "yayan@fibermedia.co.id"
                        ],
                        "nama": "Yayan Anwar",
                        "npwp": "18273814123"
                    },
                    {
                        "alamat": "Rumah anwar",
                        "email": [
                            "anwar@tachyon.net.id",
                            "anwar@remala.co.id"
                        ],
                        "nama": "Khoirul Anwar",
                        "npwp": "18273814123"
                    },
                    {
                        "alamat": "Rumah jaya",
                        "email": [
                            "jaya@tachyon.net.id",
                            "jaya@remala.co.id"
                        ],
                        "nama": "Sunan Jaya",
                        "npwp": "18273814123"
                    },  
                       ]
                return jsonify(data)

        for kategori in list_kategori:
            if ptnya == kategori['pt']:
                get_id_invoice = TblTemplateInvoiceModel.query.filter_by(html=kategori['invoice']).all()
                list_id_invoice = [item.id for item in get_id_invoice]
                
                get_id_kategori = TblKategoriCustomerModel.query.filter(TblKategoriCustomerModel.template_invoice.in_(list_id_invoice)).all()
                list_kategori = [item.code for item in get_id_kategori]

                query = TblCustomer2015Model.query
                
                query = query.filter(TblCustomer2015Model.url_1.in_(list_kategori)).filter_by(disabled=0)

                if 'group_by' in kwargs:
                    if kwargs['group_by'] == 'npwp':
                        query = query.group_by(TblCustomer2015Model.npwp)
                    elif kwargs['group_by'] == 'nama_npwp':
                        query = query.group_by(TblCustomer2015Model.nama_npwp)
                    elif kwargs['group_by'] == 'alamat_npwp':
                        query = query.group_by(TblCustomer2015Model.alamat_npwp)
                    elif kwargs['group_by'] == 'nama_client':
                        query = query.group_by(TblCustomer2015Model.kepada)

                query = query.all()
                    

                for customer in query:
                    data_pembeli = customer.to_dict()
                    email_pembeli = data_pembeli['email_tagihan'].replace(';','').replace(',','')
                    list_customer_email = email_pembeli.split(' ')
                    list_email.append(
                        {
                            'nama':data_pembeli['nama_npwp'],
                            'email':list_customer_email,
                            'npwp':data_pembeli['npwp'].replace('.','').replace('-',''),
                            'alamat':data_pembeli['alamat_npwp']
                        }
                    )

        return jsonify(list_email)
