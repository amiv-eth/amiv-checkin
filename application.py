# application.py for deployment on AWS

import os

from app import create_app

config_name = 'production'

application = app = create_app(config_name, file_based_secrets=False)

if __name__ == '__main__':
    application.run()
