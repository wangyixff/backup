#! /usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/FlaskApps/catalog/")

# points to the catalog.py file
from catalog import app as application
application.secret_key = "somesecretsessionkey"
