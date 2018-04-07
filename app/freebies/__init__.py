
from flask import Blueprint

freebies_bp = Blueprint('freebies', __name__)

from . import views
