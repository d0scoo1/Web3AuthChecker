import prepare
from prepare import web3_dir, get_file_name,run,get_web3s

from web3_auth_checker.checkers import Web3Request, MsgChecker
from web3_auth_checker.web_request import WebServicePostman
from web3_auth_checker import logger_init
import logging

logger = logger_init(logging.ERROR)

# This is a mutiple process example
# This example cannot run because we don't provide the multiple config files.
file_list = get_web3s(0,30)
run(file_list, MsgChecker,logger, 15)

'''
for i in range(103,104): 
    file = get_file_name(str(i)+"_")
    if file:
        print()
        print(file)
        w3p = WebServicePostman(file)
        c = MsgSigChecker(w3p, logger)
        c.check()
        c.save_output()
'''