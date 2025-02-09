from . import db
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.sql import func

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

#db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    #notes = db.relationship('Note')
    
    def __repr__(self):
        return f'<User {self.email}>'


class UserProfile(db.Model, UserMixin):
    __tablename__ = 'user_profile'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)                   # required for standard process
    cellno = db.Column(db.String(100), unique=True, nullable=False)
    user_password = db.Column(db.String(150), nullable=False)                        # required for standard process 
    is_social_login_user = db.Column(db.Boolean, default=False, nullable=False)            # Flag for Google users
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationship to SpazaOwner
    spaza_owners = db.relationship('SpazaOwner', back_populates='user', cascade='all, delete')

    def __repr__(self):
        return f'<UserProfile {self.username}>'



class RegistrationForm(db.Model,UserMixin):
    __tablename__ = "registration_form"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'), nullable=False)
    business_type = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100),nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.DateTime, nullable=False)
    gender = db.Column(db.String(10),   nullable=False)
    id_number = db.Column(db.String(13),  nullable=False)  # South African ID number
    passport_number = db.Column(db.String(20), nullable=True)
    citizenship = db.Column(db.String(50), nullable=False)
    street_address = db.Column(db.String(100),  nullable=False)
    address2 = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(10),  nullable=False)
    province = db.Column(db.String(50), nullable=False)
    district_mnc = db.Column(db.String(50), nullable = False)  # District municipality
    status = db.Column(db.String(50), default="draft")  # "draft" or "submitted"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    user = db.relationship('UserProfile', backref='registration_form')

class RegistrationProgress(db.Model):
    __tablename__ = "registration_progress"

    id = db.Column(db.Integer, primary_key=True)  # Unique ID for the progress entry
    user_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('spazaowner.id'), nullable=True)  # Nullable initially
    form_id = db.Column(db.Integer, db.ForeignKey('registration_form.id'), nullable=False)

    # Progress tracking fields
    personal_details_completed = db.Column(db.Boolean, default=False)
    address_details_completed = db.Column(db.Boolean, default=False)
    business_details_completed = db.Column(db.Boolean, default=False)
    overall_status = db.Column(db.String(50), default="in_progress")  # "in_progress" or "completed"

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('UserProfile', backref='registration_progress')
    owner = db.relationship('SpazaOwner', backref='registration_progress')
    form = db.relationship('RegistrationForm', backref='registration_progress')

    def __repr__(self):
        return f'<RegistrationProgress user_id={self.user_id}, status={self.overall_status}>'

