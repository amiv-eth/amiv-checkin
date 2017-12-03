
from flask import Blueprint

checkin_bp = Blueprint('checkin', __name__)

from . import views
