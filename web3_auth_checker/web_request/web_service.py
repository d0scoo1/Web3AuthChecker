from typing import Dict
import copy
import json

class RequestItem():
    '''
    A request item
    '''
    def __init__(
        self,
        name:str,
        perform: str = 'skip' , # 'skip', 'request'
        input_payload: Dict = None, # web3.json
        output: Dict = None, # web3.json
        sign: Dict = None, # web3.json : "sign_before_request":true
        request_args: dict = None # postman request item
    ):

        self.name = name
        self.perform = perform
        self.input = input_payload or {}
        self.output = output or {}
        self.sign = sign or False
        self.request_args = request_args or {}
        '''
            request_args:
                method,
                url,
                headers,
                params,
                data,
                timeout,
                impersonate,
        '''
        self.response = None
        self.success = None
        self.local_context = {}
        self.session_context = {}
    
    def safe(self):
        return get_safe_request_item(self)


    def __str__(self) -> str:
        return f'name: {self.name}\nperform: {self.perform}\ninput: {self.input}\noutput: {self.output}\npsign: {self.sign}\nrequest_args: {self.request_args}\nresponse: {self.response}\nsuccess: {self.success}\nlocal_context: {self.local_context}\nsession_context: {self.session_context}\n'
    

def _format_cookies(cookies):
    #TODO: expires
    f_cookies = {}
    for c_k in cookies:
        c_v = cookies.get(c_k)
        f_cookies[c_k] = c_v
    return f_cookies

def get_safe_request_item(r:RequestItem):
    '''
    Get a safe request item
    '''
    sr = RequestItem(r.name)
    sr.perform = r.perform
    sr.input = copy.deepcopy(r.input)
    sr.output = copy.deepcopy(r.output)
    sr.sign = r.sign

    req_args = copy.deepcopy(r.request_args)
    if 'data' in req_args:
        req_args['data'] = req_args['data'].decode('utf-8') if isinstance(req_args['data'], bytes) else req_args['data']
    sr.request_args = req_args

    sr.response = None if r.response is None else{
            #'request': self.response.request.__dict__,
            'url': r.response.url,
            'content_text': r.response.text,
            'status_code': r.response.status_code,
            'reason': r.response.reason,
            'ok': r.response.ok,
            #'headers': self.response.headers.__dict__,
            'cookies': _format_cookies(r.response.cookies),
            'elapsed': r.response.elapsed,
            'encoding': r.response.encoding,
            'charset': r.response.charset,
            'redirect_count': r.response.redirect_count,
            'redirect_url': r.response.redirect_url,
        },
    
    sr.success = r.success
    sr.session_context = copy.deepcopy(r.session_context)
    sr.local_context = copy.deepcopy(r.local_context)

    return sr


class WebService():
    '''
    A web service object, including a set of request items.
    '''
    def __init__(self, ws_path:str):
        self.webservice_filename:str = ws_path.split('/')[-1].split('\\')[-1]
        self.webservice_path:str = ws_path
        self.webservice_raw = None
        self.name: str = None
        self.url: str = None
        self.request_items: dict = {} # name : RequestItem

        with open(self.webservice_path,'r',encoding='utf-8') as f:
            self.webservice_raw = json.load(f)
            self.name = self.webservice_raw['name']
            self.url = self.webservice_raw['url']
            self.auth_type = self.webservice_raw['auth_type'] # New property
        
        if self.webservice_raw['schema'] != '1.0':
            raise ImportError("Not a valid web3 file")
    
    def get_item(self, name:str):
        return self.request_items.get(name)
