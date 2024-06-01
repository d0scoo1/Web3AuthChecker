from .web_service import WebService, RequestItem
import json
import os

class WebServicePostman(WebService):
    def __init__(
        self,
        ws_file_name:str,
        ws_dir:str = './web3_postman',
        postman_dir:str = 'postmans'       
    ):
        '''
        WebService.properties
        '''
        self.ws_file_name = ws_file_name
        self.ws_dir = ws_dir
        super().__init__(os.path.join(ws_dir,ws_file_name))
        
        '''
        Postman.properties
        '''
        self.postman_file_path:str =None
        self.postman_raw:json = None

        self.postman_file_path = os.path.join(ws_dir,postman_dir, self.webservice_raw['postman_file_name'])

        with open(self.postman_file_path,'r',encoding='utf-8') as f:
            self.postman_raw = json.load(f)

        if "https://schema.getpostman.com" not in self.postman_raw['info']['schema']:
            raise ImportError("Not a valid postman json file")

        self._make_request_items()


    def _make_request_items(self):
        '''
        Combine web3.items and postman.items according name
        '''
        postman_items = self._get_postman_request_items()

        for w_name, w_item in self.webservice_raw['items'].items():
            if w_item == {}:
                self.request_items[w_name] = RequestItem(w_name)
                continue
            
            req_args = {}
            if w_name in postman_items:
                req_args = postman_items[w_name]
            
            # "impersonate" : "chrome110",
            #if 'impersonate' in w_item: req_args['impersonate'] = req_args['impersonate']
            if 'update_request_args' in w_item:
                req_args.update(w_item['update_request_args'])
            
            sign = False
            if 'sign_before_request' in w_item: sign = w_item['sign_before_request']
            
            self.request_items[w_name] = RequestItem(
                                    w_name,
                                    w_item['perform'],
                                    w_item['input'],
                                    w_item['output'],
                                    sign,
                                    req_args)

    def _get_postman_request_items(self):
        '''
        postman.items as request arguments
            method: str,
            url: str,
            headers: Dict[str, str],
            params: Optional[Dict[str, str]] = {},
            data = {},
            #files: Optional[Dict] = {}, # Not implemented
            timeout:Optional[int]= 10
        '''

        postman_items = {}

        for item in self.postman_raw['item']:
            if item == {} or 'request' not in item:
                continue
            
            item_request = item['request']

            headers = {}
            for h in item_request['header']:
                headers[h['key']] = h['value']
            #headers['User-Agent'] = 'PostmanRuntime/7.30.0' # add/replace User-Agent
            #'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.55'

            # Authorization
            if 'auth' in item['request']:
                auth = item['request']['auth']
                if auth != {} and auth['type'] != 'noauth':
                    if auth['type'] == 'bearer':
                        headers['Authorization'] = 'Bearer $$ token $$' #+ auth['bearer'][0]['token']

            # data: formdata
            data = _parse_body(item_request['body'],headers)
            # TODO: parse params
            params = {}

            postman_items[item['name']] = {
                'method': item_request['method'],
                'url': item_request['url']['raw'],
                'headers': headers,
                'params': params,
                'data': data,
                'timeout': 10,
                'impersonate':None
            }
        
        return postman_items 


def _parse_body(body,headers):
    data = {}

    if body == {} or body is None or body['mode'] not in body:
        return {}
    
    if body['mode'] == 'raw':
        data = body['raw']
    elif body['mode'] == 'formdata':
        data = {}
        for f in body['formdata']:
            data[f['key']] = f['value']
        #data = MultipartFormData.format(data, headers=headers).encode('utf-8')
        data = MultipartFormData.format(data, headers=headers)
    elif body['mode'] == 'urlencoded':
        data = ''
        for f in body['urlencoded']:
            data += f['key'] + '=' + f['value'] + '&'
        data = data[:-1]

    return data


class MultipartFormData(object):
    """
    https://zhuanlan.zhihu.com/p/535027979
    multipart/form-data格式转化
    """

    @staticmethod
    def format(data, boundary="----WebKitFormBoundaryaHKj8Ql1KX5XPkXc", headers=None) -> str:
        """
        form data
        :param: data:  {"req":{"cno":"18990876","flag":"Y"},"ts":1,"sig":1,"v": 2.0}
        :param: boundary: "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        :param: headers: 包含boundary的头信息；如果boundary与headers同时存在以headers为准
        :return: str
        :rtype: str
        """
        headers = headers or {}
        #从headers中提取boundary信息
        for key in headers.keys():
            if key.lower() == "content-type":
                fd_val = str(headers[key])
                if "boundary" in fd_val:
                    fd_val = fd_val.split(";")[1].strip()
                    boundary = fd_val.split("=")[1].strip()
                else:
                    raise Exception("multipart/form-data error, content-type key does not have boundary")
                break
        #form-data格式定式
        jion_str = '--{}\r\nContent-Disposition: form-data; name="{}"\r\n\r\n{}\r\n'
        end_str = "--{}--".format(boundary)
        args_str = ""

        if not isinstance(data, dict):
            raise Exception("multipart/form-data parameters error")
        for key, value in data.items():
            args_str = args_str + jion_str.format(boundary, key, value)
        
        args_str = args_str + end_str.format(boundary)
        #args_str = args_str.replace("\'", "\"")
        return args_str
