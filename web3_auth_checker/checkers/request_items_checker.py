from .abstract_checker import AbstractChecker
from .msg_tokenizer import TokenType, MsgTokenizer

class RequestItemsChecker(AbstractChecker):
    NAME = "request_items"
    DESCRIPTION = "Check all request items before checking the auth"

    def _check(self):
        self.results = {
            'msg_query': None,
            'auth': None,
            'settings': None,
            'logout': None,
        }
        w3r = self.create_web3_request()

        for item_name in self.REQUEST_ITEMS:
            r = self.request(w3r, item_name,None,self.context_middleware_msg)
            self.results[item_name] = r
            
            if not r:
                self.passed = False
                return
        
        self.passed = True


    def context_middleware_msg(self,session_context):
        msgTokenizer = MsgTokenizer(self.web3.url, self.web3.name)
        if "msg" in session_context:
            msgTokenizer.add_msg(session_context['msg'])
            msg = ""
            for token in msgTokenizer.tokens:
                msg = msg + token
            session_context['msg'] = msg

        return session_context
