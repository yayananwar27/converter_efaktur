from flask import jsonify, current_app, abort, request, send_file
from marshmallow import Schema, fields, ValidationError
from flask_restful import Resource
from flask_apispec.views import MethodResource
from flask_apispec import marshal_with, doc, use_kwargs
import csv
from collections import defaultdict
from apprudi.models import TblCustomer2015Model, TblCustomerInvoice2015Model
import os
from datetime import datetime
from dict2xml import dict2xml
import re
import pandas as pd
import math


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

def round_up(value):
    if value - int(value) >= 0.50:  # Jika desimal >= 0.50
        return math.ceil(value)     # Bulatkan ke atas
    else:
        return math.floor(value)    # Bulatkan ke bawah

def parse_invoices(data):
            invoice_dict = {}
            for _, row in data.iterrows():
                invoice_no = row['No Invoice 3'].strip("'")
                # current_app.logger.debug(invoice_no)
                if invoice_no not in invoice_dict:
                    bulan_id = {
                        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
                        "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
                        "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
                    }
                    hari, bulan, tahun = (row['Tgl Invoice'].strip("'")).split()
                    tanggal_konversi = f"{tahun}-{bulan_id[bulan]}-{hari.zfill(2)}"

                    pembeli_exists = TblCustomerInvoice2015Model.query.filter_by(no_invoice_1=invoice_no).first()
                    if not pembeli_exists:
                        pembeli_exists = TblCustomer2015Model.query.filter_by(kepada=row['Kepada'].strip("'")).order_by(TblCustomer2015Model.id.desc()).first()
                        if not pembeli_exists:
                            id_pel = row['ID Pelanggan'].strip("'")+' %'
                            pembeli_exists = TblCustomer2015Model.query.filter(
                                TblCustomer2015Model.alamat.like(id_pel)
                                ).order_by(TblCustomer2015Model.id.desc()).first()
                            if not pembeli_exists:
                                abort(404, row['No Invoice 3'])

                    data_pembeli = pembeli_exists.to_dict()
                    nama_pembeli = data_pembeli['kepada']
                    if data_pembeli['nama_npwp'] != None:
                        nama_pembeli = data_pembeli['nama_npwp']

                    alamat_pembeli = data_pembeli['alamat']
                    if data_pembeli['alamat_npwp'] != None:
                        alamat_pembeli = data_pembeli['alamat_npwp']

                    npwp_pembeli = data_pembeli['npwp'].replace('.','').replace('-','').replace(' ','')
                    if len(npwp_pembeli) == 15:
                        npwp_pembeli = '0'+npwp_pembeli
                    
                    try:
                        int(npwp_pembeli)
                    except Exception as e:
                        abort(500, npwp_pembeli)

                    # email_pembeli = data_pembeli['email_tagihan'].replace(';','').replace(',','')
                    # if len(email_pembeli.split(' ')) > 1:
                    #     email_pembeli = email_pembeli.split(' ')[0]

                    email_pembeli = data_pembeli['email_tagihan']
                    # if len(email_pembeli.split(' ')) > 1:
                    #     email_pembeli = email_pembeli.split(' ')[0]

                    invoice_dict[invoice_no] = {
                        'seller_tin':data_pembeli['kategori']['seller']['tin'],
                        'seller_nitku':data_pembeli['kategori']['seller']['nitku'],
                        'npwp_pembeli':npwp_pembeli,
                        'email_pembeli':email_pembeli,
                        'nama_pembeli': nama_pembeli,
                        'no_invoice': invoice_no,
                        'tgl_invoice': tanggal_konversi,
                        'alamat_pembeli': alamat_pembeli.replace('\r','').replace('\n',' '),
                        'grand_total': int(row['Grand Total'].strip("'")),
                        'total': int(row['Total'].strip("'")),
                        'pembelian': []
                    }

                harga_satuan = 0
                try:
                    qty = int(row['Qty'].strip("'"))
                    harga_satuan = int(row['Jumlah'].strip("'"))/qty
                except Exception as e:
                    current_app.logger.error(e)
                    qty = 1
                    try:
                        harga_satuan = int(row['Jumlah'].strip("'"))/qty
                    except Exception as e:
                        current_app.logger.error(e)
                        try:
                            harga_satuan = int(row['Harga Satuan'].strip("'"))
                        except Exception as e:
                            current_app.logger.error(e)
                   

                if harga_satuan < 0:
                    list_pembelian = invoice_dict[invoice_no]['pembelian']
                    for no,pembelian in enumerate(list_pembelian):
                        if 'Periode' in pembelian['keterangan']:
                            invoice_dict[invoice_no]['pembelian'][no]['diskon'] = abs(harga_satuan)
                elif harga_satuan == 0:
                    pass
                else:
                    invoice_dict[invoice_no]['pembelian'].append({
                        'keterangan': row['Keterangan'].strip("'").replace(' , ','').replace(':',' ').replace('  ',''),
                        'qty': qty,
                        'harga_satuan': harga_satuan,
                        'diskon':0
                    })
            return list(invoice_dict.values())

def process_list_inv(list_invoices):

    costum_nitku = [
        {'tin':'0353379258085000', 'nitku':'3173020407770008000000'},
        {'tin':'0015730104076000', 'nitku':'0015730104076000000003'}
    ]

    data = {'TIN':None}
    invoices = []
    for invoice in list_invoices:
        if data['TIN'] == None:
            data['TIN'] = invoice['seller_tin']
        elif data['TIN'] != invoice['seller_tin']:
            current_app.logger.error(invoice['no_invoice'])
            current_app.logger.error(f'TIN {data['TIN']} dan {invoice['seller_tin']}')
            abort(400, 'NPWP/TIN Penjual Berbeda')
        
        BuyerTin = invoice['npwp_pembeli']
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
        list_goods = []

        goods = invoice['pembelian']

        for nitku in costum_nitku:
            if BuyerTin == nitku['tin']:
                BuyerIDTKU = nitku['nitku']
                break

        total = 0
        grand_total = 0
        dpp_lain = 0
        for good in goods:
            
            qty = int(good['qty'])
            discount = good['diskon']
            tax_base = (good['harga_satuan']*qty)-discount
            other_tax_base = round(tax_base*11/12,2)
            vat = round(other_tax_base*12/100,2)

            # if invoice['no_invoice'] == 'INV/FMI-0196/01/01.25':
            #     qty = int(good['qty'])
            #     discount = good['diskon']
            #     tax_base = (good['harga_satuan']*qty)-discount
            #     other_tax_base = tax_base*11/12
            #     vat = other_tax_base*12/100
            #     print(f'{good['harga_satuan']}, {tax_base}, {other_tax_base}, {vat}, {(vat+tax_base)}')
            
            dpp_lain += other_tax_base
            total += tax_base
            grand_total += (vat+tax_base)
            
            #if invoice['no_invoice'] == 'INV/FMI-0196/01/01.25':
            # print(f'{total}, {grand_total}, {dpp_lain}')

            list_goods.append(
                {
                    'Opt':'B',
                    'Code':'000000',
                    'Name': good['keterangan'],
                    'Unit': 'UM.0024',
                    'Price': int(good['harga_satuan']),
                    'Qty':qty,
                    'TotalDiscount':int(discount),
                    'TaxBase':tax_base,
                    'OtherTaxBase':other_tax_base,
                    'VATRate':12,
                    'VAT':vat,
                    'STLGRate':0,
                    'STLG':0
                }
            )

        if round(invoice['total'], 2) != total:
            current_app.logger.error(invoice['no_invoice'])
            current_app.logger.error(f'{invoice["total"]} != {total}')    
            abort(400, 'Ada yanga salah di total')

        if round(invoice['grand_total'],2) != int(round_up(grand_total)):
            current_app.logger.error(invoice['no_invoice'])
            if round(invoice['grand_total'],2) != int(round_up(grand_total)+10000):
                current_app.logger.error(f'{invoice["grand_total"]} != {round(grand_total, 2)}')
                current_app.logger.error(f'{invoice["grand_total"]} != {round(grand_total+10000, 2)}')
                abort(400, 'Ada yang salah di Grand Total')

        invoices.append(
            {
                'TaxInvoiceDate': invoice['tgl_invoice'],
                'TaxInvoiceOpt': 'Normal',
                'TrxCode':'04',
                'AddInfo': None,
                'CustomDoc': None,
                'RefDec': invoice['no_invoice'],
                'FacilityStamp': None,
                'SellerIDTKU':invoice['seller_nitku'],
                'BuyerTin': BuyerTin,
                'BuyerDocument': BuyerDoc,
                'BuyerCountry': 'IDN',
                'BuyerDocumentNumber': BuyerDocNum,
                'BuyerName': invoice['nama_pembeli'],
                'BuyerAdress': invoice['alamat_pembeli'],
                'BuyerEmail':invoice['email_pembeli'],
                'BuyerIDTKU':BuyerIDTKU,
                'ListOfGoodService':[
                    {'GoodService':list_goods}
                ]
            }
        )

    data['ListOfTaxInvoice'] = {'TaxInvoice':invoices}
    return data

def generate_xml(buyer_with_items):
    #xml_body = dict2xml(buyer_with_items)
    #xml_body_cleaned = re.sub(r"<(\w+)>None</\1>", r"<\1 />", xml_body)
    list_taxinvoice = buyer_with_items['ListOfTaxInvoice']['TaxInvoice']

    xml_taxinvoice = ''
    for taxinvoice in list_taxinvoice:
        xml_goods = ''
        list_goods = taxinvoice['ListOfGoodService'][0]['GoodService']
        for good in list_goods:
            xml_goods += f'''                <GoodService>
                    <Opt>{good['Opt']}</Opt>
                    <Code>{good['Code']}</Code>
                    <Name>{good['Name']}</Name>
                    <Unit>{good['Unit']}</Unit>
                    <Price>{good['Price']}</Price>
                    <Qty>{good['Qty']}</Qty>
                    <TotalDiscount>{good['TotalDiscount']}</TotalDiscount>
                    <TaxBase>{good['TaxBase']}</TaxBase>
                    <OtherTaxBase>{good['OtherTaxBase']}</OtherTaxBase>
                    <VATRate>{good['VATRate']}</VATRate>
                    <VAT>{good['VAT']}</VAT>
                    <STLGRate>{good['STLGRate']}</STLGRate>
                    <STLG>{good['STLG']}</STLG>
                </GoodService>
'''
        
        AddInfo = '<AddInfo/>'
        if taxinvoice['AddInfo'] != None:
            AddInfo = f"<AddInfo>{taxinvoice['AddInfo']}</AddInfo>"

        CustomDoc = '<CustomDoc/>'
        if taxinvoice['CustomDoc'] != None:
            CustomDoc = f"<CustomDoc>{taxinvoice['CustomDoc']}</CustomDoc>"

        RefDesc = '<RefDesc/>'
        if taxinvoice['RefDec'] != None:
            RefDesc = f"<RefDesc>{taxinvoice['RefDec']}</RefDesc>"
            
        FacilityStamp = '<FacilityStamp/>'
        if taxinvoice['FacilityStamp'] != None:
            FacilityStamp = f"<FacilityStamp>{taxinvoice['FacilityStamp']}</FacilityStamp>"

        BuyerEmail = '<BuyerEmail/>'
        if taxinvoice['BuyerEmail'] != None:
            BuyerEmail = f"<BuyerEmail>{taxinvoice['BuyerEmail']}</BuyerEmail>"

        xml_taxinvoice += f'''        <TaxInvoice>
            <TaxInvoiceDate>{taxinvoice['TaxInvoiceDate']}</TaxInvoiceDate>
            <TaxInvoiceOpt>{taxinvoice['TaxInvoiceOpt']}</TaxInvoiceOpt>
            <TrxCode>{taxinvoice['TrxCode']}</TrxCode>
            {AddInfo}
            {CustomDoc}
            {RefDesc}
            {FacilityStamp}
            <SellerIDTKU>{taxinvoice['SellerIDTKU']}</SellerIDTKU>
            <BuyerTin>{taxinvoice['BuyerTin']}</BuyerTin>
            <BuyerDocument>{taxinvoice['BuyerDocument']}</BuyerDocument>
            <BuyerCountry>{taxinvoice['BuyerCountry']}</BuyerCountry>
            <BuyerDocumentNumber>{taxinvoice['BuyerDocumentNumber']}</BuyerDocumentNumber>
            <BuyerName>{taxinvoice['BuyerName']}</BuyerName>
            <BuyerAdress>{taxinvoice['BuyerAdress']}</BuyerAdress>
            {BuyerEmail}
            <BuyerIDTKU>{taxinvoice['BuyerIDTKU']}</BuyerIDTKU>
            <ListOfGoodService>
{xml_goods}            </ListOfGoodService>
        </TaxInvoice>
'''
    
    xml_output = f"""<?xml version='1.0' encoding='utf-8'?>
<TaxInvoiceBulk xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">
    <TIN>{buyer_with_items['TIN']}</TIN>
    <ListOfTaxInvoice>
{xml_taxinvoice}    </ListOfTaxInvoice>
</TaxInvoiceBulk>"""
    return xml_output

class ConverterCsvApi(MethodResource, Resource):
    @doc(description='Converter CSV', tags=['Converter'])
    @use_kwargs(UploadCsvSchema, location=('files'))
    def post(self, **kwargs):
        file = kwargs['file_csv']
        if not file:
            abort('invalid file')

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        file_path = os.path.join(UPLOAD_FOLDER, f"{timestamp}.csv")
        #file_path = 'file_invoice_search_full.csv'
        file.save(file_path)
        # Load the CSV file
        df = pd.read_csv(file_path)
        # Clean and normalize column names
        df.columns = df.columns.str.strip()

        df = df.sort_values(by='Jumlah', key=lambda x: x.str.strip("'").astype(float), ascending=False)

        # Apply the transformation
        invoice_data = parse_invoices(df)
        current_app.logger.debug('INVOICE CSV SSELESAI')
        data = process_list_inv(invoice_data)
        current_app.logger.debug('INVOICE PROSES SELESAI')
        #return jsonify(data)
        
        xml_output = generate_xml(data)

        output_path = os.path.join(UPLOAD_FOLDER, f"{data['TIN']}_{timestamp}.xml")
        with open(output_path, 'w') as f:
            f.write(xml_output)

        return send_file(output_path, as_attachment=True, download_name=f"result_{data['TIN']}_{timestamp}.xml")
