import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import get_appsettings
from pyramid.paster import setup_logging

from ..models import DBSession
from ..models import Page
from ..models import Dog
from ..models import Base

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd)) 
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    with transaction.manager:
        page = Page('FrontPage', 'This is the front page')
        DBSession.add(page)

        dog = Dog('Trilly', 2, 'bastardino')
        DBSession.add(dog)
