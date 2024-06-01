from .abstract_checker import AbstractChecker

import time
SLEEP_TIME = 60
class MsgSigChecker(AbstractChecker):
    NAME = "msg_sig_security"
    DESCRIPTION = "Check msg signature security"

    def _check(self):
        self.results = {
            'URL_NOT_IN_MSG': None,
            'NAME_NOT_IN_MSG': None,
            "NONCE_NOT_IN_MSG": None,

            "NOT_CHECK_MSG": None,
            "NOT_CHECK_MSG_BODY": None,
            "NOT_CHECK_NONCE": None,
            "NOT_CHECK_SIG": None,

            "SIG_CAN_REPLAY": None,
            "SIG_FIRST_APPEAR": None,

            "MSG1": None,
            "MSG2": None,
            "NONCE_1": None,
            "NONCE_2": None,
            "MSG_BODY_1": None,
            "MSG_BODY_2": None,
            #'NONCE_TYPE':None, # Random or Timestamp
            "SIG_1": None,
            "SIG_2": None,

            #"CHECK_PADDING_HEAD": False,
            #"CHECK_PADDING_TAIL": False,

            "INFO":{
                "NOT_CHECK_MSG":{
                    "MSG":None,
                    "SIG":None,
                },
                "NOT_CHECK_MSG_BODY":{
                    "MSG":None,
                    "SIG":None,
                },
                "NOT_CHECK_NONCE":{
                    "MSG":None,
                    "SIG":None,
                },
                "NOT_CHECK_SIG":{
                    "MSG":None,
                    "SIG":None,
                },
            }
        }

        self._msg_info()
        time.sleep(SLEEP_TIME)

        #1: Fake msg
        self._check_msg()
        time.sleep(SLEEP_TIME)
        
        self._check_msg_body()
        if self.results['NOT_CHECK_MSG_BODY'] is not None: # If not runned, skip the waiting
            time.sleep(SLEEP_TIME)
        
        self._check_nonce()
        if self.results['NOT_CHECK_NONCE'] is not None:
            time.sleep(SLEEP_TIME)
        self._check_sig()

        self.logger.info(self.results)

        self.passed = True

    def _msg_info(self):
        w3r1 = self.create_web3_request()
        for item in ['msg_query', 'auth', 'settings']:
            if not self.request(w3r1, item):
                self.passed = False
                return False

        if "msg" in w3r1.session.session_context:
            self.results['MSG1'] = w3r1.session.session_context['msg']
        if "msg_body" in w3r1.session.session_context:
            self.results['MSG_BODY_1'] = w3r1.session.session_context['msg_body']
            self.results['NOT_CHECK_MSG_BODY'] = True # For check_msg_body
        if "nonce" in w3r1.session.session_context:
            self.results['NONCE_1'] = w3r1.session.session_context['nonce']
            self.results['NOT_CHECK_NONCE'] = True # For check_nonce

        if "sig" in w3r1.session.session_context:
            self.results['SIG_1'] = w3r1.session.session_context['sig']
        
        time.sleep(SLEEP_TIME)
        w3r2 = self.create_web3_request()
        for item in ['msg_query', 'auth', 'settings']:
            if not self.request(w3r2, item):
                self.passed = False
                return False
            if self.results['SIG_FIRST_APPEAR'] is None and 'sig' in w3r2.session.session_context:
                    self.results['SIG_FIRST_APPEAR'] = item

        
        if "msg" in w3r2.session.session_context:
            self.results['MSG2'] = w3r2.session.session_context['msg']
        else:
            return
        if "msg_body" in w3r2.session.session_context:
            self.results['MSG_BODY_2'] = w3r2.session.session_context['msg_body']
        if "nonce" in w3r2.session.session_context:
            self.results['NONCE_2'] = w3r2.session.session_context['nonce']
        if "sig" in w3r2.session.session_context:
            self.results['SIG_2'] = w3r2.session.session_context['sig']

        self.results['NAME_NOT_IN_MSG'] = True
        if self.web3.name.lower() in self.results['MSG1'].lower():
            self.results['NAME_NOT_IN_MSG'] = False
            
        self.results['URL_NOT_IN_MSG'] = True
        if self.web3.url.lower() in self.results['MSG1'].lower():
            self.results['URL_NOT_IN_MSG'] = False            
        
        self.results['NONCE_NOT_IN_MSG'] = True
        if self.results['MSG1'] != self.results['MSG2']:
            self.results['NONCE_NOT_IN_MSG'] = False

        # SIG_CAN_REPLAY
        self.results['SIG_CAN_REPLAY'] = False
        item = self.results['SIG_FIRST_APPEAR']
        if self.request_again(w3r2, item):
            self.results['SIG_CAN_REPLAY'] = True


    def _check_msg(self):
        self.results['NOT_CHECK_MSG'] = True
        w3r = self.create_web3_request()
        local_context = {'msg': 'fake_msg'}
        for item in ['msg_query', 'auth', 'settings']:
            if not self.request(w3r, item, local_context):
                self.results['NOT_CHECK_MSG'] = False
                break
        self.results['INFO']['NOT_CHECK_MSG']['MSG'] = w3r.session.session_context['msg']
        self.results['INFO']['NOT_CHECK_MSG']['SIG'] = w3r.session.session_context['sig']
    
    def _check_msg_body(self):
        # AFTER _msg_info

        if self.results['NOT_CHECK_MSG_BODY'] is None:
            return

        w3r = self.create_web3_request()
        local_context = {'msg_body': 'fake_body'}
        for item in ['msg_query', 'auth', 'settings']:
            if not self.request(w3r, item, local_context):
                self.results['NOT_CHECK_MSG_BODY'] = False
                break
        
        self.results['INFO']['NOT_CHECK_MSG_BODY']['MSG'] = w3r.session.session_context['msg']
        self.results['INFO']['NOT_CHECK_MSG_BODY']['SIG'] = w3r.session.session_context['sig']

    def _check_nonce(self):
        if self.results['NOT_CHECK_NONCE'] is None:
            return

        w3r = self.create_web3_request()
        local_context = {'nonce': 'fake_nonce'}
        for item in ['msg_query', 'auth', 'settings']:
            if not self.request(w3r, item, local_context):
                self.results['NOT_CHECK_NONCE'] = False
                break
        
        self.results['INFO']['NOT_CHECK_NONCE']['MSG'] = w3r.session.session_context['msg']
        self.results['INFO']['NOT_CHECK_NONCE']['SIG'] = w3r.session.session_context['sig']

    def _check_sig(self):
        self.results['NOT_CHECK_SIG'] = True
        w3r = self.create_web3_request()
        local_context = {'sig':'0x13d6babe50ad4056b7a768ed1dbe1b7a8fab35b3a598b324c202ccf3f7c5dbde78c633df080ffb17b7aea6bd0bc7901c280986c81fa406bd8d93faf5912d4d291c'} #'fake sig' account[0]
        for item in ['msg_query', 'auth', 'settings']:
            if not self.request(w3r, item, local_context):
                self.results['NOT_CHECK_SIG'] = False
                break
        
        self.results['INFO']['NOT_CHECK_SIG']['MSG'] = w3r.session.session_context['msg']
        self.results['INFO']['NOT_CHECK_SIG']['SIG'] = w3r.session.session_context['sig']

    '''
    def _check_padding_head(self):
        w3r = self.create_web3_request()
        local_context = {'msg': 'fake_head $$ msg $$'}
        for item in ['msg_query', 'auth', 'settings']:
            if not self.request(w3r, item, local_context):
                self.results['CHECK_PADDING_HEAD'] = True
                return
    
    def _check_padding_tail(self):
        w3r = self.create_web3_request()
        local_context = {'msg': '$$ msg $$ fake_tail'}
        for item in ['msg_query', 'auth', 'settings']:
            if not self.request(w3r, item, local_context):
                self.results['CHECK_PADDING_TAIL'] = True
                return
    '''