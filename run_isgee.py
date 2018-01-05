# application.py for deployment on AWS

import os

from app import create_app

config_name = 'prod_isgee'

app = create_app(config_name, file_based_secrets=True)

if __name__ == '__main__':
    app.run()
