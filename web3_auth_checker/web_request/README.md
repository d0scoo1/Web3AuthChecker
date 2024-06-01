We set up a configuation file for each postman file.
The configuration file is a JSON file that contains the following information:

```json
{
    "schema": "1.0",
    "name":"", // The name of the web service
    "url":"", // The url of the web service
    "postman_file_name":"", // The postman file name
    "items":{
        "msg_query":{  // request name
            "perform":"request", // perform type: request, skip
            "input":{ // These data will be loaded into the request
                "addr": "0x1234...", // this keyword will be fill in the msg. Keywords only fill once, so cannot recurse
                "msg":"Please sign this message\n Address:$$ addr $$ Nonce is $$ nonce $$",
            },
            "output":{ // The output will be loaded into the next request
                /**
                json,path:{"kw":[]}
                state:200
                text
                html:html.text
                */
                "output":{ 
                "type":"json",
                "path":{
                    "nonce":["results","nonce"] // The nonce will be added to the session context
                }
            },
            },
            "update_request_args":{
                "impersonate": "chrome110", // set the impersonate
                "timeout": 10,
                "params":{}  // You can even update the params
            },
            "perform_conf":{} //perform config 
        },


        "auth":{
            "perform":"request", // request, input, skip
            "input":{  },
            "output":{ 
                "type":"json",
                "path":{
                    "token":["results","accessToken"] // The path of the message
                }
            },
            "update_request_args":{
                "impersonate": "chrome110", // set the impersonate
            },
            "perform_conf":{
                "sign_before_request":true
            } //perform config 
        },

        "settings":{
            "perform":"request", // request, input, skip
            "input":{  },
            "output":{ 
                "type":"state",
                "code": 200
            },
            "update_request_args":{
                "impersonate": "chrome110", // set the impersonate
            },
        },
    }
}
```