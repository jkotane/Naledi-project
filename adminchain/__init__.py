from flask import Blueprint

# Initialize admin blueprint
admin_bp = Blueprint("admin", __name__)
adminauth = Blueprint("adminauth", __name__, url_prefix="/adminauth")

# Import routes AFTER initializing blueprint
from adminchain import adminroutes
