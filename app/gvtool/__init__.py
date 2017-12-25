
from flask import Blueprint

gvtool_bp = Blueprint('gvtool', __name__)

from . import views
