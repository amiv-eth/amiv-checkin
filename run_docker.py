# wsgi server (used in docker container)
# [bjoern](https://github.com/jonashaag/bjoern) required.

import os
from app import create_app
import bjoern

config_name = 'prod_isgee'

if __name__ == '__main__':
    print('Starting bjoern on port 8080...', flush=True)
    bjoern.run(create_app(config_name, file_based_secrets=True), '0.0.0.0', 8080)

