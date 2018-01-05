# config.py

import os


class Config(object):
    """
    Common configurations
    """

    # Put any configurations here that are common across all environments
    AMIV_API_URL = "https://amiv-api.ethz.ch"


class DevelopmentConfig(Config):
    """
    Development configurations
    """

    DEBUG = True
    SQLALCHEMY_ECHO = True
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMPLATES_AUTO_RELOAD = True

    SECURITY_NUM_PROXY_LEVELS = 0
    SECURITY_MAX_FAILED_LOGIN_TRIES = 5
    SECURITY_UNBANNABLE_SUBNETS = ['129.132.0.0/16', '127.0.0.1/32']


def cl(obj):
    if obj is None:
        return ""


class AWSConfig(Config):
    """
    Production configurations
    """

    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECURITY_NUM_PROXY_LEVELS = 1
    SECURITY_MAX_FAILED_LOGIN_TRIES = 5
    SECURITY_UNBANNABLE_SUBNETS = ['129.132.0.0/16']

    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://'\
                                + cl(os.getenv('RDS_USERNAME')) + ':' + cl(os.getenv('RDS_PASSWORD'))\
                                + '@' + cl(os.getenv('RDS_HOSTNAME'))\
                                + '/' + cl(os.getenv('RDS_DB_NAME'))
    SECRET_KEY = os.getenv('SECRET_KEY')


class ISGEEConfig(Config):
    """
    Production configurations
    """

    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECURITY_NUM_PROXY_LEVELS = 0
    SECURITY_MAX_FAILED_LOGIN_TRIES = 5
    SECURITY_UNBANNABLE_SUBNETS = ['129.132.0.0/16']


app_config = {
    'development': DevelopmentConfig,
    'prod_aws': AWSConfig,
    'prod_isgee': ISGEEConfig
}
