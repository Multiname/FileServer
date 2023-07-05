from app import db
from datetime import datetime

class FileInfo(db.Model):
    __tablename__ = 'files_info'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    extension = db.Column(db.String(10), nullable=False)
    size = db.Column(db.Integer(), nullable=False)
    path = db.Column(db.String(), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime(), nullable=True)
    comment = db.Column(db.String(300), nullable=True)

    def __repr__(self):
        return '<{}:{}>'.format(self.id, self.name)