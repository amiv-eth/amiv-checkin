
from flask import Blueprint

mutate_bp = Blueprint('mutate', __name__)

from . import views
