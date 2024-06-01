from .abstract_checker import AbstractChecker
from .msg_tokenizer import TokenType, MsgTokenizer
from ..web_request.web_session import sign_msg

import time
SLEEP_TIME = 60
class MsgChecker(AbstractChecker):
    NAME = "msg_security"
    DESCRIPTION = "Check msg security"

    def _check(self):
        self.results = {
            # Design
            "URL_NOT_IN_MSG": True,
            "NAME_NOT_IN_MSG": True,
            "NONCE_NOT_IN_MSG": True,
            
            # Implementation
            "FAKE_MSG": None, # Fake msg + Nonce
            "REPLACE_URL": None, # Replace url
            "REPLACE_NAME": None, # Replace name
            "ADD_statement": None, # Add statement in msg
            
            "MSGS": [],
        }

        self.msgTokenizer = MsgTokenizer(self.web3.url, self.web3.name)

        self._request_msg()
        time.sleep(SLEEP_TIME)
        self._request_msg()
        # After 2 times request, we have 2 msg, and we can get nonce from msg
        t_labels = self.msgTokenizer.labels
        for t_label in t_labels:
            if t_label == TokenType.statement:
                continue
            if t_label == TokenType.domain:
                self.results['URL_NOT_IN_MSG'] = False
            elif t_label == TokenType.websiteName:
                self.results['NAME_NOT_IN_MSG'] = False
            elif t_label.value >= 400 and t_label.value < 500:
                self.results['NONCE_NOT_IN_MSG'] = False
        
        # Fake msg
        self._request_ge('FAKE_MSG', self.context_middleware_fake_msg)

        # Replace url
        if self.results['URL_NOT_IN_MSG'] == False:
            self._request_ge('REPLACE_URL', self.cm_replace_url)

        # Replace name
        if self.results['NAME_NOT_IN_MSG'] == False:
            self._request_ge('REPLACE_NAME', self.cm_replace_name)

        # Add statement
        self._request_ge('ADD_statement', self.cm_add_statement)

        # Nonce
        #self.nonces_request()

        self.logger.info(self.results)

        self.passed = True


    def _request_msg(self):
        w3r1 = self.create_web3_request()
        for item in ['msg_query', 'auth', 'settings']:
            time.sleep(3)
            if not self.request(w3r1, item):
                self.passed = False
                return False
        
        if "msg" in w3r1.session.session_context:
            msg = w3r1.session.session_context['msg']
            self.msgTokenizer.add_msg(msg)
            self.results['MSGS'].append(('request_msg',msg))


    def _request_ge(self, result, context_middleware):
        time.sleep(SLEEP_TIME)
        w3r = self.create_web3_request()
        for item in ['msg_query', 'auth', 'settings']:
            time.sleep(3)
            if not self.request(w3r, item, None, context_middleware):
                self.results[result] = False
                return
        self.results[result] = True

    def context_middleware_fake_msg(self,session_context):
        if "msg" not in session_context:
            return session_context

        self.results['MSGS'].append(('before_fake_msg',session_context['msg']))

        self.msgTokenizer.add_msg(session_context['msg'])
        tokens = self.msgTokenizer.tokens
        labels = self.msgTokenizer.labels

        msg = "fake msg"
        for i, label in enumerate(labels):
            if label.value >= 400 and label.value < 500:
                msg += tokens[i]
        
        self.results['MSGS'].append(('fake_msg',msg))
        
        session_context['msg'] = msg
        session_context['sig'] = sign_msg(msg, session_context['private_key'])

        return session_context

    def cm_replace_url(self, session_context):
        if "msg" not in session_context:
            return session_context

        self.msgTokenizer.add_msg(session_context['msg'])
        tokens = self.msgTokenizer.tokens
        labels = self.msgTokenizer.labels

        msg = ""
        for i, label in enumerate(labels):
            if label == TokenType.domain:
                msg += "http://fake.com"#tokens[i].replace(self.web3.url,"fake.com")
            else:
                msg += tokens[i]
        
        self.results['MSGS'].append(('replace_url',msg))
        session_context['msg'] = msg
        session_context['sig'] = sign_msg(msg, session_context['private_key'])

        return session_context


    def cm_replace_name(self, session_context):
        if "msg" not in session_context:
            return session_context

        self.msgTokenizer.add_msg(session_context['msg'])
        tokens = self.msgTokenizer.tokens
        labels = self.msgTokenizer.labels

        msg = ""
        for i, label in enumerate(labels):
            if label == TokenType.websiteName:
                msg += "fake_name"#tokens[i].replace(self.web3.name,"fake")
            else:
                msg += tokens[i]
        
        self.results['MSGS'].append(('replace_name',msg))
        session_context['msg'] = msg
        session_context['sig'] = sign_msg(msg, session_context['private_key'])

        return session_context

    def cm_add_statement(self, session_context):
        if "msg" not in session_context:
            return session_context

        msg = "something" + session_context['msg']

        self.results['MSGS'].append(('add_statement',msg))
        session_context['msg'] = msg
        session_context['sig'] = sign_msg(msg, session_context['private_key'])

        return session_context

    def nonces_request(self):
        if(self.results['NONCE'] != True):
            return

        tokens = self.msgTokenizer.tokens
        labels = self.msgTokenizer.labels
        for label, token in zip(labels, tokens):
            if label.value >= 400 and label.value < 500:
                self.results['NONCES']['NONCE_TYPE'] = label.name
                self.results['NONCES']['VALUE'] = token