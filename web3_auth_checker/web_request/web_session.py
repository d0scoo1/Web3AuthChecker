from typing import Dict, List, Optional, Tuple, Union, cast
from curl_cffi import requests
from curl_cffi.requests import Session
import time
import json
import copy
import base64
from .web_service import WebService

class WebSession():
    '''
    The Websession manages requests and responses.
    '''
    def __init__(
        self,
        session_context: dict = None, # global context
        session: Session = None, # requests.Session()
    ):

        self.session_context = session_context or {}
        self.session = session or requests.Session()

        self.before_request_items = []
        self.after_request_items = []

    def request(
        self,
        item: WebService, # RequestItem
        _local_context:dict=None,
        context_middleware = None
    ):
        '''
        Perform a request

        Args:
            item (RequestItem): The request item
            local_context (dict, optional): The local context. Defaults to None.
        '''
        if item == None: 
            raise Exception('Request item is None')

        local_context = {}
        if _local_context:
            local_context = copy.deepcopy(_local_context)
        
        item.local_context = local_context
        self.before_request_items.append(item.safe())
        
        '''
            item.input -> overwrite -> session_context
            local_context -> overwrite -> input -> overwrite -> session_context
        '''
        temp_context = copy.deepcopy(self.session_context)
        temp_context.update(item.input) # overwrite
        temp_context.update(local_context) # overwrite

        temp_context = _fill_data(temp_context, temp_context) # fill local_context, session_context, item.input
        temp_context = _fill_data(temp_context, temp_context)
        temp_context = _fill_data(temp_context, temp_context) # max support depth 3

        if "sig" not in local_context:
            if item.sign:
                temp_context['sig'] = sign_msg(temp_context['msg'], temp_context['private_key'])
        
        if context_middleware is not None:
            temp_context = context_middleware(temp_context)
    
        self.session_context = temp_context
        item.session_context = copy.deepcopy(self.session_context)
        item.output = _fill_data(item.output,temp_context)
        

        if item.perform == 'skip':
            return True
        
        if 'url' not in item.request_args: 
                raise Exception(f'Request args incorrectly: {{item.request_args}}')
        
        if item.perform == 'request':
            request_args = _fill_data(item.request_args,temp_context)

            _check_fill_data(request_args)
            return self._request_perform(request_args, item)
    
    def request_again(self,item, local_context:dict=None,context_middleware = None):
        
        self.before_request_items.append(item.safe())
        if item.perform == 'skip': return True
        if item.perform == 'request': return self._request_perform(item.request_args, item)
        return False

    def _request_perform(self, request_args, item):
        
        # curl_cffi : data must be dict, BytesIO or bytes
        if type(request_args['data']) == str:
            request_args['data'] = request_args['data'].encode('utf-8')
  
        #print('-----------------request_args-----------------\n',request_args)

        if "SLEEP" in item.input:
            time.sleep(item.input['SLEEP'])

        if 'NEW_SESSION' in item.input and item.input['NEW_SESSION'] == True:
            self.session = requests.Session()
        response = self.session.request(**request_args)

        # check output
        success = True
        if not response.ok:
            success = False
        else: 
            text = response.text
            #print(text)
            if item.output['type'] == 'json':
                try:
                    if "split_head" in item.output:
                        text = text[item.output['split_head']:]
                    if "split_tail" in item.output:
                        text = text[:item.output['split_tail']]
                    text = json.loads(text)
                    success = _update_session_context_by_response(self.session_context,text,item.output['path'])
                except Exception as exception:
                    #print(exception)
                    success = False
                
            elif item.output['type'] == 'state':
                if item.output['code'] != response.status_code:
                    success = False
            elif item.output['type'] == 'text':
                #if item.output['text'] != text:
                    #success = False
                self.session_context['text'] = text
            elif item.output['type'] == 'html':
                if item.output['html'] not in text:
                    success = False
            elif item.output['type'] == 'url':
                response.content = b"" # clear content
                if item.output['url'] != response.url:
                    success = False
        
        item.request_args = request_args
        item.response = response
        item.success = success
        item.session_context = copy.deepcopy(self.session_context)

        self.after_request_items.append(item.safe())
        return success
    


from eth_account.messages import encode_defunct
from eth_account import Account
def sign_msg(msg, private_key, print_msg=False):
    '''
    Sign message with private key
    '''
    if print_msg:
        print('---------msg------------')
        print(repr(msg))

    msg = encode_defunct(text=msg)
    account = Account.from_key(private_key)
    sig =  account.sign_message(msg)

    if print_msg:
        print('---------sig------------')
        print(sig.signature.hex())
    return sig.signature.hex()

import re

def _fill_data(d, context,print_msg=False):
    '''
    Fill data by context
    
    input <-fill- session_context
    session_context <-update- input

    local_context <-fill- session_context
    session_context <-update- local_context 

    request_args <-fill- session_context
   
    '''
    if type(context) != dict:
        raise Exception('Invalid type: %s' % type(context))
    
    text = ''
    if type(d) == dict:
        text = json.dumps(d)
    elif type(d) == str:
        text = d
    else:
        raise Exception('Invalid request args type: %s' % type(d))
    
    kws = re.findall(r'\$\$.*?\$\$', text)
    for kw in kws:
        key = kw[2:-2].strip()
        if key.startswith('eval:'): # eval
            val = eval(key[5:])
            val = str(val)
            text = text.replace(kw,val)
        else:
            if key in context:
                val = context[key]
                val = str(val)
                val = val.replace('"','\\\\\\\"').replace('\n','\\\\n').replace('\r','\\\\r') # only format the value
                text = text.replace(kw,val)
            else: 
                continue
                #raise Exception('Key not found: %s' % key) 
        if print_msg:
            print(f'kw:{kw}->val:{val}')
    return json.loads(text, strict=False)


def _check_fill_data(d):
    '''
    before request, check if all data is filled
    '''
    if type(d) == dict:
        text = json.dumps(d)
    elif type(d) == str:
        text = d
    else:
        raise Exception('Invalid request args type: %s' % type(d))
    
    kws = re.findall(r'\$\$.*?\$\$', text)
    if len(kws) > 0:
        print('-----------------request_args-----------------')
        print(text)
        raise Exception('Key not found:',kws[0][2:-2].strip() )
    return True


def _update_session_context_by_response(session_context,response,output_path):
    '''
    update session_context with response
    '''

    for key, paths in output_path.items():
        t_rsp = response
        for path in paths:
            if path not in t_rsp:
                return False
            t_rsp = t_rsp[path]
        session_context[key] = t_rsp
    return True

def _web3_auth(msg, private_key):
    sig = sign_msg(msg, private_key)
    web3 = {"signature":sig,"body":msg}
    print('---------web3------------')
    print(web3)
    web3_token = base64.b64encode(json.dumps(web3).encode('utf-8')).decode('utf-8')
    return web3_token

def _msg_base64(msg):
    return base64.b64encode(msg.encode('utf-8')).decode('utf-8')