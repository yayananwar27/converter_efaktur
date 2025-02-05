from config import db

class TblCustomerInvoice2015Model(db.Model):
    __bind_key__ = 'dbrudi'
    __tablename__ = 'customer_invoice_2015'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer)
    no_invoice_1 = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        name_exists = TblCustomer2015Model.query.filter_by(id=self.customer_id).first()
        return name_exists.to_dict()

class TblCustomer2015Model(db.Model):
    __bind_key__ = 'dbrudi'
    __tablename__ = 'customer_2015'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kepada = db.Column(db.String(255), unique=True, nullable=False)
    email_tagihan = db.Column(db.Text, nullable=True)
    url_1 = db.Column(db.String(255), nullable=True)
    alamat = db.Column(db.Text, nullable=True)
    npwp = db.Column(db.String(255), nullable=True)
    nama_npwp = db.Column(db.String(255), nullable=True)
    alamat_npwp = db.Column(db.Text, nullable=True)
    disabled = db.Column(db.Integer, default=False)

    def to_dict(self):
        data = {
            'id':self.id,
            'kepada':self.kepada,
            'email_tagihan':self.email_tagihan,
            'alamat':self.alamat,
            'nama_npwp':self.nama_npwp,
            'alamat_npwp':self.alamat_npwp,
            'npwp':self.npwp,
            'disabled':self.disabled
        }
        kateg_exists = TblKategoriCustomerModel.query.filter_by(code=self.url_1).first()
        if kateg_exists:
            kategori = kateg_exists.template_inv()
            data['kategori'] = kategori
        return data

class TblKategoriCustomerModel(db.Model):
    __bind_key__ = 'dbrudi'
    __tablename__ = 'kategori_customer'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(255), unique=True, nullable=False)
    template_invoice = db.Column(db.String(255), nullable=False)

    def template_inv(self):
        data = {
            'id':self.id,
            'code':self.code,
            'template_invoice':self.template_invoice
        }
        template_exists = TblTemplateInvoiceModel.query.filter_by(id=self.template_invoice).first()
        if template_exists:
            tmplt_npwp = template_exists.npwp()
            data['seller'] = tmplt_npwp
        return data
        
    
class TblTemplateInvoiceModel(db.Model):
    __bind_key__ = 'dbrudi'
    __tablename__ = 'template_invoice'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    html = db.Column(db.Text, nullable=True)

    def npwp(self):
        from appconverter.models import TblNpwpSellerModel
        npwp_exist = TblNpwpSellerModel.query.filter_by(npwp_html=self.html).first()
        if npwp_exist:
            return npwp_exist.to_dict()