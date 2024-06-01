import re
import datetime
import enum

class TokenType(enum.Enum):
    statement = 101
    domain = 201
    websiteName = 202
    address = 301

    nonce = 400
    rnd = 401
    timestamp10 = 402
    timestamp13 = 403
    datetime = 404


class MsgTokenizer():
    def __init__(self, _domain = None, _website_name =None, _step = 5):
        self.domain = _domain.lower()  # lower case
        self.website_name = _website_name.lower()  # lower case
        self.step = _step
        self.msgs = []
        self.tokenss = []
        self.labelss = []

    def add_msg(self, msg):
        self._split_msg(msg)
        

    def _split_msg(self, msg):

        tokens = re.split(r'(https://|http://|/|\s+)', msg) #[ \f\n\r\t\v]
        
        # check tokenss length
        if len(self.tokenss) > 0:
            if len(self.tokenss[0]) != len(tokens):
                #raise Exception("The length of tokenss is not equal")
                return

        self.msgs.append(msg)

        labels = []
        for token in tokens:
            if self.domain is not None and self.domain in token.lower():
                labels.append(TokenType.domain)
            elif self.website_name is not None and self.website_name in token.lower():
                labels.append(TokenType.websiteName)
            elif token.lower().startswith('0x'):
                labels.append(TokenType.address)
            else:
                labels.append(TokenType.statement)
        
        self.tokenss.append(tokens)
        self.labelss.append(labels)

        #Update nonce
        if len(self.tokenss) < 2:
            return
        
        step = self.step # Check 5 messages each time
        if len(self.tokenss) < step:
            step = len(self.tokenss)

        for i in range(len(self.tokenss[-1])):
            same_tokens = []
            for j in range(0,step):
                same_tokens.append(self.tokenss[-1-j][i]) # get the ith token of jth tokens
            if len(set(same_tokens)) == 1:
                continue
            self.labelss[-1][i] = TokenType.nonce
        
        last_tokens = self.tokenss[-1]
        last_labels = self.labelss[-1]
        
        for i, label in enumerate(last_labels):
            if label != TokenType.nonce:
                continue

            token = last_tokens[i]
            if len(token) == 10:
                try:
                    token = int(token)
                    if token > 1225468800: # 2008-11-01
                        last_labels[i] = TokenType.timestamp10
                        continue
                except ValueError:
                    pass
            
            if len(token) == 13:
                try:
                    token = int(token)
                    if token > 1225468800000: # 2008-11-01
                        last_labels[i] = TokenType.timestamp13
                        continue
                except ValueError:
                    pass

            if len(token) == 24 or len(token) == 25 : #'2023-01-14T09:20:11.703Z'
                try:
                    data = datetime.datetime.strptime(token[:23], '%Y-%m-%dT%H:%M:%S.%f')
                    if data.year > 2008:
                        last_labels[i] = TokenType.datetime
                    continue
                except ValueError:
                    pass
            
            last_labels[i] = TokenType.rnd

        #self.labelss[-1] = last_labels

    @property
    def msg(self):
        if len(self.msgs) == 0:
            return None
        return self.msgs[-1]

    @property
    def tokens(self):
        if len(self.tokenss) == 0:
            return None
        return self.tokenss[-1]
    
    @property
    def labels(self):
        if len(self.labelss) == 0:
            return None
        return self.labelss[-1]