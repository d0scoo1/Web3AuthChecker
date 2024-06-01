import sys
sys.path.append('./')

from web3_auth_checker.checkers import Web3Request
from web3_auth_checker.web_request import WebServicePostman
from web3_auth_checker import logger_init
import logging

logger = logger_init(logging.DEBUG)

ws_dir = 'examples'
ws = WebServicePostman('0_opensea.io.json',ws_dir)

# print the request items in the config file
for k,v in ws.request_items.items():
    print(k)

# Web3AuthChecker encapsulates Flexrequest, so you can use Web3Request instead of WebSession to send requests
w3r = Web3Request(ws, logger)
# keys in local_context are used to replace the variables in the request items
local_context = {'addr':'0x36E7C6FeB20A90b07F63863D09cC12C4c9f39064','private_key': 'f78411d5886f5ded63cd304b9b56dd87b05ce0922223e87b4927cc56bfaa7b02'}
w3r.request('msg_query', local_context) # request item in the config file
w3r.request('auth')
w3r.request('settings')
w3r.request('logout')