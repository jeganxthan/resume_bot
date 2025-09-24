from db import db
import uuid
from sqlalchemy.dialects.postgresql import JSON

class Resume(db.Model):
    __tablename__ = "resumes"
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    resume_json = db.Column(JSON, nullable=False)

    def __repr__(self):
        return f"<Resume {self.id} - {self.api_key}>"
