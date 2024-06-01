import sys
sys.path.append('./')
from web3_auth_checker.checkers import TEST_ACCOUNTS
from web3_auth_checker.web_request import sign_msg


real_sig = '0xa07c6ccc55e447af2ca9ae34c7b2300555893395fcba0f4c81dfcb703d842f9e4e66ace9cb48b90fad1b5262ebb60eac3bff012733e3dfa362d7088ee4ab5f2e1c'

#0xeebaC884E95349DD24C6935B5c4E171Ed91c7f50

msg = 'Welcome to Paragraph! \n\nClick to sign in.\n\nThis request will not trigger a blockchain transaction or cost any gas fees.\n\nHere is your nonce: nyWJ8o92GZ7Dk77KjtGRlw==\n'
sign_msg(msg,TEST_ACCOUNTS[0]['private_key'],True)
