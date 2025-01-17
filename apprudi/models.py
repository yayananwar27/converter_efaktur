from config import db

class TblCustomer2015Model(db.Model):
    __bind_key__ = 'dbrudi'
    __tablename__ = 'customer_2015'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kepada = db.Column(db.String(255), unique=True, nullable=False)
    email_tagihan = db.Column(db.Text, nullable=True)
    url_1 = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        data = {
            'id':self.id,
            'kepada':self.kepada,
            'email_tagihan':self.email_tagihan
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