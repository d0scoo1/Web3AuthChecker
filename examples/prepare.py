import os
import sys
sys.path.append('./')


web3_dir = 'examples'
def get_file_name(file_startswith: str) -> str:
    for file in os.listdir(web3_dir):
        if file.endswith(".json") and file.startswith(file_startswith):
            return file
    return None


'''

'''
from multiprocessing import Process,Queue
from tqdm import tqdm

def producer(q,file_list):
    for c in tqdm(file_list):
        q.put(c)

def consumer(q,checker,logger):
    while 1:
        c = q.get()
        if c:
            ch = checker(c,logger)
            ch.check()
            ch.save_output()
        else:
            return

def run(file_list, checker,logger, process_num = 4):
    q = Queue(process_num)
    p = Process(target=producer,args=(q,file_list,))
    consumers = [Process(target=consumer,args=(q,checker,logger)) for i in range(process_num)]

    tasks = [p] + consumers
    for t in tasks:
        t.start() 
    p.join()
    for i in range(process_num): q.put(None)

from web3_auth_checker.web_request import WebServicePostman
def get_web3s(startswith, endswith):
    file_list = []
    for i in range(startswith,endswith): 
        file = get_file_name(str(i)+"_")
        if file:
            w3p = WebServicePostman(file)
            file_list.append(w3p)
    
    print("File Nums:",len(file_list))
    return file_list
    
#file_list = ['1','2','3','4','5','6','7','8','9','10']
#run(file_list, Checker, 2)