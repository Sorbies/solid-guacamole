#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/solid-guacamole")
sys.stdout.write("Hello")

from app import create_app
application = create_app()
application.secret_key = 'Add your secret key'
