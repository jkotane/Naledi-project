from flask import Blueprint
from . import spachainauth, spachainview  # Ensure routes are imported

# Create Blueprints
spachainauth = Blueprint('spachainauth', __name__, url_prefix='/spazachain/auth')
spachainview = Blueprint('spachainview', __name__, url_prefix='/spazachain/view')

# Import routes to register them with the Blueprint
from . import spachainauth, spachainview  # Ensure routes are imported
