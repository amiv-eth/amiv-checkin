
import secrets
from flask import Blueprint


login_bp = Blueprint('login', __name__)


def generate_secure_pin():
    return 10000000 + secrets.randbelow(90000000)


from . import views

