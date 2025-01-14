from flask import Flask, request, jsonify, send_file, render_template
import os
import csv
import re
from datetime import datetime
from collections import defaultdict
from dict2xml import dict2xml

def process_efaktur_csv(file_path, Tin):
    buyers = []
    goods = defaultdict(list)

    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)

        current_buyer = None

        for num, row in enumerate(reader):
            if num == 0:
                pass
            elif row[0] == 'FK':
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
                        BuyerDoc = 'National ID'
                        BuyerDocNum = BuyerTin
                        BuyerTin = '0000000000000000'
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
                    'SellerIDTKU':str(Tin)+'000000',
                    'BuyerTin': BuyerTin,
                    'BuyerDocument': BuyerDoc,
                    'BuyerCountry': 'IDN',
                    'BuyerDocumentNumber': BuyerDocNum,
                    'BuyerName': row[8],
                    'BuyerAddress': row[9],
                    'BuyerEmail':None,
                    'BuyerIDTKU':BuyerIDTKU,
                }
                buyers.append(buyer_data)
                current_buyer = row[8]

            elif row[0] == 'OF' and current_buyer is not None:
                good_data = {
                    'Opt':'B',
                    'Code':'000000',
                    'Name': row[2],
                    'Unit': 'UM.0024',
                    'Price': float(row[5]),
                    'Qty':float(row[4]),
                    'TotalDiscount':float(row[6]),
                    'TaxBase':float(row[7]),
                    'OtherTaxBase':float(row[7])*11/12,
                    'VATRate':12,
                    'VAT':(float(row[7])*11/12)*12/100,
                    'STLGRate':0,
                    'STLG':0
                }
                goods[current_buyer].append(good_data)

    return buyers, goods

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

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['file']
        Tin = request.form['Tin']

        if not file or len(Tin) != 16:
            return jsonify({"error": "Invalid file or TIN"}), 400

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        file_path = os.path.join(UPLOAD_FOLDER, f"{Tin}_{timestamp}.csv")
        file.save(file_path)

        buyers, goods = process_efaktur_csv(file_path, Tin)
        List_items = generate_buyer_with_items(buyers, goods)
        buyer_with_items = {'TIN': Tin, 'ListOfTaxInvoice':{'TaxInvoice':List_items}}
        xml_output = generate_xml(buyer_with_items)

        output_path = os.path.join(UPLOAD_FOLDER, f"{Tin}_{timestamp}.xml")
        with open(output_path, 'w') as f:
            f.write(xml_output)

        return send_file(output_path, as_attachment=True, download_name=f"result_{Tin}_{timestamp}.xml")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
