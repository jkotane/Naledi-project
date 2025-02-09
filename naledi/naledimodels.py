#from . import db
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.sql import func
from flask_sqlalchemy import SQLAlchemy
from .extensions import db

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
    user_type = db.Column(db.String(50), nullable=False)  # "spaza_owner" or "mnc_official"
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



class SpazaOwner(db.Model, UserMixin):
    __tablename__ = 'spazaowner'

    id = db.Column(db.Integer, primary_key=True)  # Primary key
    name = db.Column(db.String(45), nullable=False)
    surname = db.Column(db.String(45), nullable=False)
    email = db.Column(db.String(45), unique=True, nullable=False)
    address = db.Column(db.String(45), nullable=False)
    said = db.Column(db.String(13), nullable=False)  # SA ID

    # Foreign key to UserProfile
    user_id = db.Column(db.Integer, db.ForeignKey('user_profile.id', ondelete='CASCADE'), nullable=False)

    # Relationship to UserProfile
    user = db.relationship('UserProfile', back_populates='spaza_owners')

    def __repr__(self):
        return f'<SpazaOwner {self.name} {self.surname}>'



class Lesee(db.Model, UserMixin):
    __tablename__ = 'lesee'

    id = db.Column(db.Integer, primary_key=True)
    leseefname = db.Column(db.String(45), nullable=False)
    leseelname = db.Column(db.String(45), nullable=False)
    leseeemail = db.Column(db.String(45), unique=True, nullable=False)
    leseeaddress = db.Column(db.String(45), nullable=False)
    lesee_id = db.Column(db.String(45), nullable=False)  # Identity number or document ID
    leseestoreid = db.Column(db.Integer, db.ForeignKey('store_details.id'), nullable=False)  # Links to StoreDetails
    spazaownerid = db.Column(db.Integer, db.ForeignKey('spazaowner.id'), nullable=False)  # Links to SpazaOwner

    # Relationships
    store = db.relationship('StoreDetails', backref='lesee')  # Allows accessing lessee from a store
    owner = db.relationship('SpazaOwner', backref='lesees')  # Allows accessing all lessees for an owner

    def __repr__(self):
        return f"<Lesee {self.leseefname} {self.lesseelname}>"


class StoreDetails(db.Model,UserMixin):
    __tablename__ = 'store_details'

    id = db.Column(db.Integer, primary_key=True)
    permitid = db.Column(db.String(13), unique=True, nullable=False)
    cicpno = db.Column(db.String(13), unique=True, nullable=False)
    sarsno = db.Column(db.String(13), unique=True, nullable=False)
    zonecertno = db.Column(db.String(13), unique=True, nullable=False)
    storetype = db.Column(db.String(150), nullable=False)
    compstatus = db.Column(db.String(150), nullable=False)
    ownershipstatus = db.Column(db.String(150), nullable=False)
    storeaddress = db.Column(db.String(150), nullable=False)
    storevolume = db.Column(db.String(150), nullable=False)
    store_name = db.Column(db.String(150), nullable=False)
    reg_status = db.Column(db.String(10), default="draft")
    city = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(10),  nullable=False)
    province = db.Column(db.String(50), nullable=False)
    district_mnc = db.Column(db.String(50), nullable = False)  # District municipality
    owner_id = db.Column(db.Integer, db.ForeignKey('spazaowner.id'), nullable=False)  # Match the actual table name
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<StoreDetails {self.store_name}>"
    

class FoodItems(db.Model):
    __tablename__ = 'food_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'), nullable=False)  # Link to the user
    selected_items = db.Column(db.JSON, nullable=True)  # Store selected food items as JSON
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f'<FoodItems {self.id}>'




class HealthCompliance(db.Model):
    __tablename__ = 'health_compliance'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'), nullable=False)  # Link to user table
    sanitary_facilities = db.Column(db.JSON, nullable=True)  # Store as JSON
    cleaning_facilities = db.Column(db.JSON, nullable=True)  # Store as JSON
    handwashing_stations = db.Column(db.JSON, nullable=True)  # Store as JSON
    waste_disposal = db.Column(db.JSON, nullable=True)  # Store as JSON
    food_handling = db.Column(db.JSON, nullable=True)  # Store as JSON
    food_storage = db.Column(db.JSON, nullable=True)  # Store as JSON
    food_preparation = db.Column(db.JSON, nullable=True)  # Store as JSON
    food_prep_tools = db.Column(db.JSON, nullable=True)  # Store as JSON
    employees = db.Column(db.JSON, nullable=True)  # Store as JSON for men/women/total
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f'<HealthCompliance {self.id}>'

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('UserProfile', backref=db.backref('documents', lazy=True))

    def __repr__(self):
        return f'<Document {self.filename}>'