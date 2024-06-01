import sys
sys.path.append('./')

from web3_auth_checker.web_request import WebServicePostman, WebSession

ws_dir = 'examples' # the folder of the config file
ws_config_file = '0_opensea.io.json' # config file records the request items and parameters

# Load the config file and postman file
wsp = WebServicePostman(ws_config_file , ws_dir)

# Create a request Session
ws = WebSession()

# keys in local_context are used to replace the variables in the request items
local_context = {'addr':'0x36E7C6FeB20A90b07F63863D09cC12C4c9f39064','private_key': 'f78411d5886f5ded63cd304b9b56dd87b05ce0922223e87b4927cc56bfaa7b02'}

# request the API msg_query with the local_context
ws.request(wsp.get_item('msg_query'),local_context)

# request the API auth in the config file
ws.request(wsp.get_item('auth'))

# request the API settings in the config file
ws.request(wsp.get_item('settings'))

# print the response of the request
for r in ws.after_request_items:
    for k,v in r.__dict__.items():
        print(k,':',v)
