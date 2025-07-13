# models.py
from extensions import db

class Vocabulary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    word_type = db.Column(db.String(50), nullable=False)  # loại từ (noun, verb...)
    phonetic = db.Column(db.String(100))                  # phiên âm quốc tế
    meaning_vi = db.Column(db.String(255), nullable=False) # nghĩa tiếng Việt
    meaning_en = db.Column(db.String(255))                # nghĩa tiếng Anh (nếu có)
    note = db.Column(db.Text)                             # ghi chú
    tag = db.Column(db.String(100))                       # thẻ phân loại
