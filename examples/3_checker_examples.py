import sys
sys.path.append('./')

from web3_auth_checker.checkers import MsgChecker,MsgSigChecker,NonceChecker,JWTChecker,RequestItemsChecker
from web3_auth_checker.web_request import WebServicePostman
from web3_auth_checker import logger_init
import logging

logger = logger_init(logging.ERROR)

ws_dir = 'examples'
w3p = WebServicePostman('0_opensea.io.json',ws_dir)

# Test the reuquest items in the config file
c0 = RequestItemsChecker(w3p, logger)
c0.check()
c0.save_output() # The result will be saved in the output folder


# Message Checker
c1 = MsgChecker(w3p, logger)
c1.check()
c1.save_output()

# Message Signature Checker
c2 = MsgSigChecker(w3p, logger)
c2.check()
c2.save_output()

# Nonce Checker
c3 = NonceChecker(w3p, logger)
c3.check()
c3.save_output()

# JWT Checker
c4 = JWTChecker(w3p, logger)
c4.check()
c4.save_output()

print('Done')

