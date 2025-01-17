from config import db, event

def init_db(app):
    with app.app_context():
        pass
        #TblNpwpSellerModel.__table__.create(db.engine)
        #db.create_all()

class TblNpwpSellerModel(db.Model):
    __tablename__ = 'tblnpwpseller'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama = db.Column(db.String(255), nullable=False)
    npwp = db.Column(db.String(255), nullable=False)
    npwp_html = db.Column(db.String(255), nullable=True)

    def __init__(self, nama, npwp, npwp_html=None):
        self.nama = nama
        self.npwp = None
        if len(npwp) >= 15:
            self.npwp = npwp
        self.npwp_html = npwp_html

    def to_dict(self):
        tin = self.npwp
        if len(tin) == 15:
            tin = '0'+tin
        elif len(tin) == 14:
            tin = '00'+tin

        nitku = tin+'000000'
        return {
            'id':self.id,
            'nama':self.nama,
            'npwp':self.npwp,
            'npwp_html':self.npwp_html,
            'tin':tin,
            'nitku':nitku
        }

def insert_default_seller(*args, **kwargs):
    npwp_remala = TblNpwpSellerModel('PT REMALA ABADI', '015897184432000')
    npwp_fmi = TblNpwpSellerModel('PT FIBER MEDIA INDONESIA', '312472657016000', 'file_invoice_html_fmi.tpl')
    npwp_pc24 = TblNpwpSellerModel('PT PC 24 CYBER INDONESIA', '024502072013000', 'file_invoice_html.tpl')
    npwp_saas = TblNpwpSellerModel('PT SOLUSI APLIKASI ANDALAN SEMESTA', '433577764004000')
    npwp_jfi = TblNpwpSellerModel('PT JARINGAN FIBER INDONESIA', '437214414447000')
    npwp_aksel = TblNpwpSellerModel('PT AKSELERASI INFORMASI', '400411088015000')
    
    db.session.add(npwp_remala)
    db.session.add(npwp_fmi)
    db.session.add(npwp_pc24)
    db.session.add(npwp_saas)
    db.session.add(npwp_jfi)
    db.session.add(npwp_aksel)
    
    db.session.commit()

event.listen(TblNpwpSellerModel.__table__, 'after_create', insert_default_seller)