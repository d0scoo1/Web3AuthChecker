from .abstract_checker import AbstractChecker
from .msg_tokenizer import TokenType, MsgTokenizer
from ..web_request.web_session import sign_msg

import time
SLEEP_TIME = 61
class NonceChecker(AbstractChecker):
    NAME = "nonce_security"
    DESCRIPTION = "Check nonce security"

    def _check(self):
        self.results = {
            # Design
            "NONCE_NOT_IN_MSG": True,
            "MSGS": [],
        }

        self.msgTokenizer = MsgTokenizer(self.web3.url, self.web3.name,4)

        # Nonce
        self.nonces_request(0)
        time.sleep(SLEEP_TIME)
        self.nonces_request(1)
        time.sleep(SLEEP_TIME)
        self.nonces_request(0)
        time.sleep(SLEEP_TIME)
        self.nonces_request(1)

        labels = self.msgTokenizer.labels
        for label in labels:
            if label.value >= 400 and label.value < 500:
                self.results['NONCE_NOT_IN_MSG'] = False
                break

        self.logger.info(self.results)

        self.passed = True


    def nonces_request(self, account_index = 0):
        w3r = self.create_web3_request(account_index)
        for item in ['msg_query', 'auth', 'settings']:
            if 'msg' in w3r.session.session_context:
                msg = w3r.session.session_context['msg']
                self.results['MSGS'].append(msg)
                self.msgTokenizer.add_msg(msg)

            if not self.request(w3r, item):
                self.passed = False
                return False
        

