from .abstract_checker import AbstractChecker
import base64
import time
import json

SLEEP_TIME = 61
class JWTChecker(AbstractChecker):
    NAME = "jwt_security"
    DESCRIPTION = "Json Web Token Checker"

    def _check(self):
        self.results = {
            "TOKEN_TYPE": None, # 0: None, 1: JWT
            "TOKEN":None,
            "TOKEN_LOCATION": None, # 0: None, 1: Header, 2: Cookie

            "DECODED_TOKEN":None,
            "REQUEST_TIME":None,
            "ISSUED_AT":None,
            "EXPIRES_IN":None,
            "DURATION":None, # exp - iat || exp - request_time
            "EXPIRES":None, #  expires

            "VALID_AFTER_LOGOUT":None, # 0: False, 1: True Still valid after logout
            "VALID_AT_SAME_TIME":None, # 0: False, 1: True Still valid at the same time
            "VALID_AFTER_FIRST_LOGOUT":None,
            #"TOKEN_INVALID_TYPE":None, # The ways to invalidate the token (logout, new_login, change password, etc)
           
            
            "NOT_CHECK_TOKEN_IS_EMPTY": None, # 0: False, 1: True ONLY FOR TOKEN TYPE

            "NOT_CHECK_JWT_HEAD_IS_NONE": None,
            "NOT_CHECK_JWT_SIG": None,
            "NOT_CHECK_JWT_SIG_IS_EMPTY": None,
        }

        if self.web3.auth_type.upper() == "SIG":
            self.results['TOKEN_TYPE'] = 'SIG'
            self.passed = True
            return


        if self.web3.auth_type.upper() == "TOKEN":
            self.results['TOKEN_TYPE'] = 'TOKEN'
            self._check_info()
            #NOT_CHECK_TOKEN_IS_EMPTY
            self._check_token_is_empty()
        
        if self.web3.auth_type.upper() == "JWT":
            self.results['TOKEN_TYPE'] = 'JWT'
            self._check_info()
            # NOT_CHECK_JWT_IS_EMPTY, NOT_CHECK_JWT_SIG, NOT_CHECK_JWT_SIG_IS_EMPTY
            if self.results['TOKEN_LOCATION'] == 'Header':
                self._check_jwt()

        self.passed = True
        print(self.results)


    def _check_info(self):
        w3r1 = self.create_web3_request()
        self.results['REQUEST_TIME'] = int(w3r1.session.session_context['timestamp10'])
        for item in ['msg_query', 'auth', 'settings']:
            if not self.request(w3r1, item):
                self.passed = False
                return

        # Find the token
        if "token" in w3r1.session.session_context:
            self.results['TOKEN'] = w3r1.session.session_context['token']
            self.results['TOKEN_LOCATION'] = 'Header'
            if "expires" in w3r1.session.session_context:
                self.results['EXPIRES'] = w3r1.session.session_context['expires']
        else: # search in cookies
            s_cookies = w3r1.session.session.cookies
            for c_name in s_cookies:
                c_value = s_cookies.get(c_name)
                if c_value.startswith('eyJ'):
                    self.results['TOKEN'] = c_value
                    self.results['TOKEN_LOCATION'] = 'Cookie'
                    break
        
        # Do not find the token
        if self.results['TOKEN'] is None:
            self.results['TOKEN'] = "DO NOT FIND THE TOKEN"
            self.passed = False
            return

        # JWT info
        self._decode_jwt()
        
        # VALID_AFTER_LOGOUT
        self.results['VALID_AFTER_LOGOUT'] = False
        self.request(w3r1, 'logout')
        if self.request_again(w3r1,"settings"):
            self.results['VALID_AFTER_LOGOUT'] = True

        
        #VALID_AT_SAME_TIME
        self.results['VALID_AT_SAME_TIME'] = True
        time.sleep(SLEEP_TIME)
        w3r2 = self.create_web3_request()
        
        for item in ['msg_query', 'auth', 'settings']:
            if not self.request(w3r2, item):
                self.passed = False
                return
        
        time.sleep(int(SLEEP_TIME/2))
        w3r3 = self.create_web3_request() 
        for item in ['msg_query', 'auth', 'settings']:
            if not self.request(w3r3, item):
                self.results['VALID_AT_SAME_TIME'] = False
        
        #VALID_AFTER_FIRST_LOGOUT
        self.results['VALID_AFTER_FIRST_LOGOUT'] = False
        self.request(w3r2, 'logout')

        if self.request_again(w3r3,"settings"):
            self.results['VALID_AFTER_FIRST_LOGOUT'] = True
    
           
    def _decode_jwt(self):
        if self.results['TOKEN_TYPE'] != 'JWT':
            return
        token = self.results['TOKEN']

        tokens = token.split('.')
        if len(tokens) != 3:
            return
        
        header = tokens[0]
        payload = tokens[1]
        #signature = tokens[2]

        
        header = safe_base64_decode(header)
        payload = safe_base64_decode(payload)
        
        self.results['DECODED_TOKEN'] = header + payload

        ts = []
        for v in json.loads(payload).values():
            if type(v) == int:
                if len(str(v)) == 13:
                    ts.append(int(v/1000))
                elif len(str(v)) == 10:
                    ts.append(v)
    
        if len(ts) == 1:
            self.results['EXPIRES_IN'] = ts[0]
            self.results['DURATION'] = self.results['EXPIRES_IN'] - self.results['REQUEST_TIME']
        elif len(ts) == 2:
            if ts[0] > ts[1]:
                self.results['ISSUED_AT'] = ts[1]
                self.results['EXPIRES_IN'] = ts[0]
            else:
                self.results['ISSUED_AT'] = ts[0]
                self.results['EXPIRES_IN'] = ts[1]
            self.results['DURATION'] = self.results['EXPIRES_IN'] - self.results['ISSUED_AT']

    def _check_token_is_empty(self):
        self.results['NOT_CHECK_TOKEN_IS_EMPTY'] = False
        w3r = self.create_web3_request()
        for item in ['msg_query', 'auth']:
            if not self.request(w3r, item):
                self.passed = False
                return
        
        if self.request(w3r, 'settings',{'token':''}):
            self.results['NOT_CHECK_TOKEN_IS_EMPTY'] = True

        
    def _check_jwt(self):
        time.sleep(SLEEP_TIME)
        self._check_jwt_head_is_none()
        time.sleep(SLEEP_TIME)
        self._check_jwt_sig()
        time.sleep(SLEEP_TIME)
        self._check_jwt_sig_is_empty()
    
    def _check_jwt_head_is_none(self):
        self.results['NOT_CHECK_JWT_HEAD_IS_NONE'] = False
        w3r = self.create_web3_request()
        for item in ['msg_query', 'auth']:
            if not self.request(w3r, item):
                self.passed = False
                return

        token = w3r.session.session_context['token']
        tokens = token.split('.')
        if len(tokens) != 3:
            return

        fake_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJub25lIn0.'+tokens[1]+'.'+tokens[2]
        if self.request(w3r, 'settings',{'token':fake_token}):
            self.results['NOT_CHECK_JWT_HEAD_IS_NONE'] = True
    
    def _check_jwt_sig(self):
        self.results['NOT_CHECK_JWT_SIG'] = False
        w3r = self.create_web3_request()
        for item in ['msg_query', 'auth']:
            if not self.request(w3r, item):
                self.passed = False
                return

        token = w3r.session.session_context['token']
        tokens = token.split('.')
        if len(tokens) != 3:
            return

        fake_token = tokens[0]+'.'+tokens[1]+'.AAAAAAAAAAAyjsczisuPXzAPVzPD0CnCjkxDBfaQMPg'
        if self.request(w3r, 'settings',{'token':fake_token}):
            self.results['NOT_CHECK_JWT_SIG'] = True
    
    def _check_jwt_sig_is_empty(self):
        self.results['NOT_CHECK_JWT_SIG_IS_EMPTY'] = False
        w3r = self.create_web3_request()
        for item in ['msg_query', 'auth']:
            if not self.request(w3r, item):
                self.passed = False
                return

        token = w3r.session.session_context['token']
        tokens = token.split('.')
        if len(tokens) != 3:
            return

        fake_token = tokens[0]+'.'+tokens[1]+'.'
        if self.request(w3r, 'settings',{'token':fake_token}):
            self.results['NOT_CHECK_JWT_SIG_IS_EMPTY'] = True


def safe_base64_decode(s):

    decoded_s = None
    try:
        decoded_s = base64.b64decode(s)
    except:
        try:
            decoded_s = base64.b64decode(s+'=')
        except:
            try:
                decoded_s = base64.b64decode(s+'==')
            except:
                return None

    if decoded_s == None:
        return None
    return decoded_s.decode('utf-8')