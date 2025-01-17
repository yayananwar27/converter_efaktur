from flask import jsonify, current_app, abort, request, send_file
from marshmallow import Schema, fields, ValidationError
from flask_restful import Resource
from flask_apispec.views import MethodResource
from flask_apispec import marshal_with, doc, use_kwargs
import csv
from collections import defaultdict
from apprudi.models import TblCustomer2015Model
import os
from datetime import datetime
from dict2xml import dict2xml
import re

def validate_file(file):
    if not file:
        raise ValidationError("No file was uploaded.")
    if not file.filename.endswith('.csv'):
        raise ValidationError("The file must have a .csv extension.")
    if file.content_type not in ['text/csv', 'application/vnd.ms-excel']:
        raise ValidationError("Invalid file type. Only CSV files are allowed.")
    
class UploadCsvSchema(Schema):
    file_csv = fields.Raw(type='file', required=True, metadata={"description":"File CSV E-Faktur"}, validate=validate_file)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def process_efaktur_csv(file_path):
    buyers = []
    goods = defaultdict(list)

    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        
        current_buyer = None


        tin = None
        sellernitku = None
        buyer_email = None
        
        for num, row in enumerate(reader):
            if num == 0:
                pass
            elif row[0] == 'FK':
                #check nomor tin
                buyername = row[8]
                name_exist = TblCustomer2015Model.query.filter_by(
                    kepada=buyername).order_by(
                        TblCustomer2015Model.id.desc()
                    ).first()
                if name_exist:
                    _name_exists = name_exist.to_dict()
                    if tin == None:
                        tin = _name_exists['kategori']['seller']['tin']
                        sellernitku = _name_exists['kategori']['seller']['nitku']
                        buyer_email = _name_exists['email_tagihan']
                    elif tin != _name_exists['kategori']['seller']['tin']:
                        abort(f"Terdapat Invoice E-Faktur dengan NPWP/TIN berbeda {tin} dengan {_name_exists['kategori']['seller']['tin']}")
                
                # Baris FK untuk data buyer
                BuyerTin = str(row[7])
                BuyerDoc = 'TIN'
                BuyerDocNum = '-'
                if len(BuyerTin) == 15:
                    BuyerTin = '0'+BuyerTin
                    BuyerIDTKU = BuyerTin+'000000'
                elif len(BuyerTin) == 14:
                    BuyerTin = '00'+BuyerTin
                    BuyerIDTKU = BuyerTin+'000000'
                else:
                    if len(BuyerTin) == 16:
                        if BuyerTin[0] != '0':
                            BuyerDoc = 'National ID'
                            BuyerDocNum = BuyerTin
                            BuyerTin = '0000000000000000'
                            BuyerIDTKU = BuyerTin+'000000'
                        else:
                            BuyerIDTKU = BuyerTin+'000000'
                    else:
                        raise ValueError("Unknown DOC ID and Number")
                    
                buyer_data = {
                    'TaxInvoiceDate': row[6],
                    'TaxInvoiceOpt': 'Normal',
                    'TrxCode':'04',
                    'AddInfo': None,
                    'CustomDoc': None,
                    'RefDec': row[18],
                    'FacilityStamp': None,
                    'SellerIDTKU':sellernitku,
                    'BuyerTin': BuyerTin,
                    'BuyerDocument': BuyerDoc,
                    'BuyerCountry': 'IDN',
                    'BuyerDocumentNumber': BuyerDocNum,
                    'BuyerName': row[8],
                    'BuyerAddress': row[9],
                    'BuyerEmail':buyer_email,
                    'BuyerIDTKU':BuyerIDTKU,
                }
                buyers.append(buyer_data)
                buyer_email = None
                current_buyer = row[8]  # Buyer code sebagai kunci utama

            elif row[0] == 'OF' and current_buyer is not None:
                # Baris OF untuk data goods, diasosiasikan dengan buyer
                
                good_data = {
                    'Opt':'B',
                    'Code':'000000',
                    'Name': row[2],
                    'Unit': 'UM.0024',
                    'Price': round(float(row[5])),
                    'Qty':round(float(row[4])),
                    'TotalDiscount':round(float(row[6])),
                    'TaxBase':round(float(row[7])),
                    'OtherTaxBase':round(float(row[7])*11/12),
                    'VATRate':12,
                    'VAT':round((float(row[7])*11/12)*12/100),
                    'STLGRate':0,
                    'STLG':0
                }
                goods[current_buyer].append(good_data)

    return tin, buyers, goods

def generate_buyer_with_items(buyers, goods):
    ListInvoice = []

    for buyer in buyers:
        buyer_name = buyer['BuyerName']
        ListInvoice.append({
            'TaxInvoiceDate': buyer['TaxInvoiceDate'],
            'TaxInvoiceOpt': buyer['TaxInvoiceOpt'],
            'TrxCode':buyer['TrxCode'],
            'AddInfo': buyer['AddInfo'],
            'CustomDoc': buyer['CustomDoc'],
            'RefDec': buyer['RefDec'],
            'FacilityStamp': buyer['FacilityStamp'],
            'SellerIDTKU':buyer['SellerIDTKU'],
            'BuyerTin': buyer['BuyerTin'],
            'BuyerDocument': buyer['BuyerDocument'],
            'BuyerCountry': buyer['BuyerCountry'],
            'BuyerDocumentNumber': buyer['BuyerDocumentNumber'],
            'BuyerName': buyer['BuyerName'],
            'BuyerAddress': buyer['BuyerAddress'],
            'BuyerEmail':buyer['BuyerEmail'],
            'BuyerIDTKU':buyer['BuyerIDTKU'],
            'ListOfGoodService':[
                {'GoodService':goods.get(buyer_name, [])}
            ]
        })
    return ListInvoice

def generate_xml(buyer_with_items):
    xml_body = dict2xml(buyer_with_items)
    xml_body_cleaned = re.sub(r"<(\w+)>None</\1>", r"<\1 />", xml_body)
    xml_output = f"""<?xml version='1.0' encoding='utf-8'?>
<TaxInvoiceBulk xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">
{xml_body_cleaned}
</TaxInvoiceBulk>"""
    return xml_output


class ConverterCsvApi(MethodResource, Resource):
    @doc(description='Converter CSV', tags=['Converter E-Faktur'])
    @use_kwargs(UploadCsvSchema, location=('files'))
    def post(self, **kwargs):
        file = kwargs['file_csv']
        print(file)
        if not file:
            abort('invalid file')

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        file_path = os.path.join(UPLOAD_FOLDER, f"{timestamp}.csv")
        file.save(file_path)

        Tin, buyers, goods = process_efaktur_csv(file_path)
        List_items = generate_buyer_with_items(buyers, goods)
        buyer_with_items = {'TIN': Tin, 'ListOfTaxInvoice':{'TaxInvoice':List_items}}
        xml_output = generate_xml(buyer_with_items)

        output_path = os.path.join(UPLOAD_FOLDER, f"{Tin}_{timestamp}.xml")
        with open(output_path, 'w') as f:
            f.write(xml_output)

        return send_file(output_path, as_attachment=True, download_name=f"result_{Tin}_{timestamp}.xml")
        
    @doc(description='Get data converter CSV', tags=['Converter E-Faktur'])
    def get(self):
        from apprudi.models import TblCustomer2015Model

        all_data = TblCustomer2015Model.query.first()
        return jsonify(all_data.to_dict())
        