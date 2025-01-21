import pandas as pd

# Load the CSV file
file_path = 'file_invoice_search.csv'
df = pd.read_csv(file_path)

# Clean and normalize column names
df.columns = df.columns.str.strip()

# Define the function to transform the data
def parse_invoices(data):
    invoice_dict = {}
    for _, row in data.iterrows():
        invoice_no = row['No Invoice 3'].strip("'")
        if invoice_no not in invoice_dict:
            invoice_dict[invoice_no] = {
                'No Invoice': invoice_no,
                'Tgl Invoice': row['Tgl Invoice'].strip("'"),
                'Alamat': row['Alamat'].strip("'"),
                'Pembelian': []
            }
        invoice_dict[invoice_no]['Pembelian'].append({
            'Keterangan': row['Keterangan'].strip("'"),
            'Qty': int(row['Qty'].strip("'")),
            'Harga Satuan': float(row['Harga Satuan'].strip("'"))
        })
    return list(invoice_dict.values())

# Apply the transformation
invoice_data = parse_invoices(df)
print(invoice_data)
