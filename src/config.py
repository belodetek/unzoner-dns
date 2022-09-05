# -*- coding: utf-8 -*-

import os

DEFAULT_A = os.getenv('DEFAULT_A', '174.138.72.255')
DEFAULT_AAAA = os.getenv('DEFAULT_AAAA', '2604:a880:800:10::128:6001')
API_VERSION = os.getenv('API_VERSION', '1.0')
TARGET_COUNTRY = os.getenv('TARGET_COUNTRY', 'United States')
API_SECRET = os.getenv('API_SECRET', None)
API_HOST = os.getenv('API_HOST', 'https://api.unzoner.com')
DEBUG = int(os.getenv('DEBUG', 1))
DEFAULT_TRIES = int(os.getenv('DEFAULT_TRIES', 3))
DEFAULT_DELAY = int(os.getenv('DEFAULT_DELAY', 2))
DEFAULT_BACKOFF = int(os.getenv('DEFAULT_BACKOFF', 2))
DNS_DOMAIN = os.getenv('DNS_DOMAIN', 'blackbox.unzoner.com.')
LISTEN_ADDR = os.getenv('LISTEN_ADDR', '0.0.0.0')
PORT = int(os.getenv('PORT', 53))
MGMT_HOST = os.getenv('MGMT_HOST', 'mgmt.unzoner.com')
DNS_TTL = int(os.getenv('DNS_TTL', 60)) # seconds
