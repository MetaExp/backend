import os
from logging.config import dictConfig

# algorithms
RESEARCH_MODE = "research"
BASELINE_MODE = "baseline"
# development
RANDOM_STATE = 42  # change it to something random if it should not be reconstructive.
# server
REACT_PORT = 3000
API_PORT = 8000
SERVER_PATH = 'localhost'
# Data sets
RATED_DATASETS_PATH = os.path.join('rated_datasets')
MOCK_DATASETS_DIR = os.path.join('tests', 'data')
# Configuration for sessions saved on the file system
SESSION_CACHE_DIR = os.path.join('tmp', 'sessions')
SESSION_THRESHOLD = 500
SESSION_MODE = '0700'
# Redis Configuration
REDIS_PORT = 6379
REDIS_HOST = '172.16.74.65'
#!!!!!!!!!!!!!!!!!!!!!!!!PLEASE LEAVE THERE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#REDIS_HOST = '172.16.19.193'
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
REDIS_PASSWORD = None
PARALLEL_EXISTENCE_TEST_PROCESSES = 12

LOG_DIR = 'log'

MAX_META_PATH_LENGTH = 6

"""{
    'name': 'Freebase',
    'url': 'https://hpi.de/mueller/metaexp-demo-neo4j-2',
    'bolt-url': 'bolt://172.20.14.22:7717',
    'username': 'neo4j',
    'password': 'neo4j'
},"""

AVAILABLE_DATA_SETS = [
    {
        'name': 'Helmholtz',
        'url': 'http://172.16.74.65:7474',
        'bolt-url': 'bolt://172.16.74.65:7687',
        'username': 'neo4j',
        'password': 'test'
    }
]


def set_up_logger():
    log_dir = 'log'
    filename = 'debug.log'
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s from %(name)s: %(message)s',
        }},
        'handlers': {
            'default': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': 'DEBUG'
            },
            'file': {
                'class': 'logging.FileHandler',
                'formatter': 'default',
                'filename': os.path.join(log_dir, filename),
                'mode': 'w',
                'level': 'DEBUG'
            },
        },
        'loggers': {
            'MetaExp': {
                'handlers': ['default', 'file']
            }
        },
        'root': {
            'level': 'DEBUG',
            'handlers': []
        },
    })
