# application.py for deployment on AWS

from app import create_app

config_name = 'production'
application = app = create_app(config_name)

if __name__ == '__main__':
    application.run()
