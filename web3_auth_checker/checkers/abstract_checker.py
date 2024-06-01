import abc
import json
import os
from logging import Logger
from typing import Optional, List, TYPE_CHECKING, Dict, Union, Callable
import copy
import time

from web3_auth_checker.web_request import WebSession, WebService, RequestItem


TEST_ACCOUNTS = [
    {'private_key': 'f78411d5886f5ded63cd304b9b56dd87b05ce0922223e87b4927cc56bfaa7b02',
    'addr': '0x36E7C6FeB20A90b07F63863D09cC12C4c9f39064',
    'addr_low': '0x36e7c6feb20a90b07f63863d09cc12c4c9f39064',
    'addr_up': '0x36E7C6FEB20A90B07F63863D09CC12C4C9F39064'
    },
    
    {'private_key': '32dfebf1b058471b80abc5434ee7229a19c870b2c85797afdbf1fb21dccaf3cd',
    'addr': '0x3BB5DdC2703B0C2a82952f25c521BE95dC9dee37',
    'addr_low': '0x3bb5ddc2703b0c2a82952f25c521be95dc9dee37',
    'addr_up': '0x3BB5DDC2703B0C2A82952F25C521BE95DC9DEE37'
    },
    
    {'private_key': '070175b068eeda71a5fab6dbd0bab9ee4ea3123729278f9ea7c192e408ac4385',
    'addr': '0xeebaC884E95349DD24C6935B5c4E171Ed91c7f50',
    'addr_low': '0xeebac884e95349dd24c6935b5c4e171ed91c7f50',
    'addr_up': '0xEEBAC884E95349DD24C6935B5C4E171ED91C7F50'
    },
]

class Web3Request():
    def __init__(
            self, 
            web3:WebService, 
            logger: Logger, 
            account_index = 0
        ) -> None:
        
        self.web3 = copy.deepcopy(web3)
        self.logger = logger

        if account_index >= len(TEST_ACCOUNTS) or account_index < 0:
            raise ValueError(f'account_index {account_index} is out of range')
        
        # Construct the session context
        timestamp  =  time.time()
        session_context = {
            # set timestamp in session_context
            "timestamp10" : str(int(timestamp)),
            "timestamp13" : str(int(timestamp*1000)),
            "ftime_ia": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(timestamp)),
            "ftime_et": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(timestamp+86400)),
        }
        session_context.update(TEST_ACCOUNTS[account_index])

        self.session = WebSession(session_context) # add the acount to the session context

    def _request(self, request_fun, item_name, local_context = None, context_middleware = None):
        '''
        Perform a request
        '''
        # Get the request item
        
        item = self.web3.get_item(item_name)
        if item is None:
            raise ValueError(f'No request item named {item_name}')

        self.logger.log(41,f'Web3Request: {self.web3.name} - {item_name} - {item.perform}')

        success = request_fun(item, local_context, context_middleware)

        if success and item.perform != 'skip':
            self.logger.debug(f'Web3Request: {self.web3.name} - {item_name} - {success} \n {item.request_args}')
            self.logger.debug(f'Response: {item.response.status_code}: {item.response.text}')
        
        if not success:
            if item.response is not None:
                self.logger.warn(f'Web3Request: {self.web3.name} - {item_name} - Response: {item.response.status_code}: {item.response.text}')
            self.logger.warn(f'Web3Request: {self.web3.name} - {item_name}:\n {item.session_context}')
            self.logger.debug(f'Web3Request: {self.web3.name} - {item_name} - {success} \n {item.request_args}')

        return success
    
    def request(self, item_name, local_context = None, context_middleware = None):
        return self._request(self.session.request, item_name, local_context, context_middleware)

    def request_again(self, item_name):
        return self._request(self.session.request_again, item_name)

    def get_item(self, item_name):
        return self.web3.get_item(item_name)



class AbstractChecker(abc.ABC):
    NAME = "Abstract Checker"
    DESCRIPTION = ""

    REQUEST_ITEMS = ['msg_query','auth','settings','logout']

    def __init__(
        self,
        web_service: WebService,
        logger: Logger,
    ):
        self.web3 = web_service
        self.logger = logger
        self.logger.name = self.NAME

        self.passed = False
        self.request_failed = []
        self.results = []

        self.w3Requests = []
        

    @abc.abstractmethod
    def _check(self):
        '''
        This is the function to be implemented by the implementing class.
        '''
        pass
      
    def check(self):
        self._check()
        if self.passed:
            self.logger.info(f'{self.web3.name} - \033[1;32mPASS\033[0m')
        else:
            self.logger.warn(f'{self.web3.name} - \033[1;31mFAIL\033[0m')
        
        return self.passed

    def create_web3_request(self, account_index = 0):
        '''
        Create a web3 session with the account index
        '''
        w3r = Web3Request(self.web3, self.logger, account_index)
        self.w3Requests.append(w3r)
        return w3r

    def request(self, w3r, item_name, local_context = None, context_middleware = None):
        r = False
        try:
            r = w3r.request(item_name, local_context, context_middleware)
        except Exception as e:
            #pass
            print(e)

        if not r:
            self.request_failed.append(item_name)
            return False
        return True

    def request_again(self, w3r, item_name):
        r = False
        try:
            r = w3r.request_again(item_name)
        except Exception as e:
            pass
        if not r:
            self.request_failed.append(item_name)
            return False
        return True
    
    def get_item(self, item_name):
        return self.web3.get_item(item_name)
    @property
    def output(self):
        '''
        Output the results of the detector
        '''
        before_request_history = []
        after_request_history = []

        for w3r in self.w3Requests:
            for item in w3r.session.before_request_items:
                before_request_history.append(item.__dict__)
            for item in w3r.session.after_request_items:
                after_request_history.append(item.__dict__)

        return {
            'detector': self.NAME,
            'description': self.DESCRIPTION,
            'passed': self.passed,
            'request_failed': self.request_failed,
            'results': self.results,
            'after_request_history': after_request_history,
            'before_request_history': before_request_history,
        }

    def save_output(self, output_dir: str = './outputs'):
        '''
        Save the output of the detector to the output directory
        '''
        output_dir = os.path.join(output_dir, time.strftime("%Y-%m-%d"))
        
        detector_dir = os.path.join(output_dir, self.NAME)

        if not os.path.exists(detector_dir):
            os.makedirs(detector_dir)


        file_name = self.web3.webservice_filename

        print(file_name)
        file_path = os.path.join(detector_dir, file_name)
        with open(file_path, 'w',encoding="UTF-8") as f:
            json.dump(self.output, f, indent=4)
