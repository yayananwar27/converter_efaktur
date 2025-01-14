import csv
from collections import defaultdict
from dict2xml import dict2xml

try:
    # Fungsi untuk membaca CSV dan memproses data
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
                    current_buyer = row[8]  # Buyer code sebagai kunci utama

                elif row[0] == 'OF' and current_buyer is not None:
                    # Baris OF untuk data goods, diasosiasikan dengan buyer
                    
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

    # Fungsi untuk menghasilkan output list of dict setiap buyer beserta itemnya
    def generate_buyer_with_items(buyers, goods):
        ListInvoice = []

        for buyer in buyers:
            buyer_name = buyer['BuyerName']
            ListInvoice.append({'TaxInvoice':{
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
            }})
        data = {'ListOfTaxInvoice':ListInvoice}
        return ListInvoice

    # Jalankan fungsi dengan file CSV yang diunggah
    Tin = '0015897184432000'
    if len(Tin) != 16:
        raise ValueError("TIN Tidak 16 karakter")
    
    file_path = 'efaktur_import_test.csv'
    buyers, goods = process_efaktur_csv(file_path, Tin)



    # Hasilkan output list of dict setiap buyer dengan itemnya
    buyer_with_items = {
        'TIN':Tin
    }
    List_items = generate_buyer_with_items(buyers, goods)
    buyer_with_items['ListOfTaxInvoice'] = List_items
    xml_body = dict2xml(buyer_with_items)
    # Bersihkan nilai 'None' dari elemen XML
    import re
    xml_body_cleaned = re.sub(r"<(\w+)>None</\1>", r"<\1 />", xml_body)
    xml_output = f"""
<?xml version='1.0' encoding='utf-8'?>
<TaxInvoiceBulk xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    {xml_body_cleaned}
</TaxInvoiceBulk>"""

    print(xml_output)
except Exception as e:
    print(e)