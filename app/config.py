import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class devConfig(object):

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'aj8hdljsdakl4qhk24e21cjn!Ew@fhffghfghggg4565t@dsa'
    SQLALCHEMY_DATABASE_URI =  'sqlite:///' + os.path.join(basedir, 'app.db') #os.environ.get('DATABASE_URL') or \
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = False
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'


class Config(object):

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'adljsakljqk2s4e21cjn!Ew@fhfghfghggg4565t@dsa'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = False
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'