# run.py

import os

from app import create_app

config_name = os.getenv('FLASK_CONFIG')
if config_name is None:
    config_name = 'development'
app = create_app(config_name)

#Use this to only run the app on this device, it cannot be accessed over the network
#if __name__ == '__main__':
#    app.run()

#Use this to run the app so it can be accessed externally
if __name__ == '__main__':
    app.run(host='0.0.0.0')
