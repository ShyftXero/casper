#!/usr/bin/env python3

from rich.console import Console
console = Console()
print = console.log # hijack the print

from requests_html import HTMLSession
import toml
import typer
import faker

import datetime
import subprocess
import time
import glob
import random
import multiprocessing
import threading
# import shlex
import uuid
import json
import socket
import smtplib
import ssl
from typing import List
from pathlib import Path


app = typer.Typer() # for cli operations


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("1.1.1.1", 80))
AGENT_IP = s.getsockname()[0]
AGENT_UUID = uuid.uuid3(uuid.NAMESPACE_DNS, str(uuid.getnode())).hex # based on mac address


DEBUG=True 

OPS = []

BEACON = True # disable the beacon with ./casper_client --no-beacon


C2_BEACON_ENDPOINT = 'http://localhost:5000/beacon' # for beaconing stats about operations to casper_server.py

@app.callback()
def options(beacon:bool=True, c2_beacon_endpoint:str='http://localhost:5000/beacon', debug:bool=True ):
    global BEACON
    global C2_BEACON_ENDPOINT
    global DEBUG

    if beacon:
        BEACON = beacon
    if c2_beacon_endpoint != C2_BEACON_ENDPOINT:
        C2_BEACON_ENDPOINT = c2_beacon_endpoint
    if debug:
        DEBUG = debug



def jitter(jitter_amount=0) -> int:
    if jitter_amount == 0:
        return 0
    return random.randint(jitter_amount * -1, jitter_amount)


def delay(base_time, jitter):
    if jitter != 0:
        jitter = jitter(jitter_amount=jitter)

    time.sleep(base_time + jitter)


@app.command()
def beacon(interval:int=5, jitter_amount:int=0 ):
    """only send beacons"""
    if BEACON == False:
        return
    while True:
        BEACON_PAYLOAD = {
            'uuid': AGENT_UUID,
            'time': str(datetime.datetime.now()),
            'ip': AGENT_IP
        }
        print(f'beacon payload: {BEACON_PAYLOAD}')

        sess = HTMLSession()
        r = sess.post(C2_BEACON_ENDPOINT, json=BEACON_PAYLOAD)
        print(f'beacon: {r}')
        time.sleep(interval + jitter(jitter_amount=jitter_amount))

def in_time_range(hours_of_operation:List[str]) -> bool:
    if hours_of_operation == None:
        return True

    start_time = hours_of_operation[0]
    end_time = hours_of_operation[1]

    current = datetime.datetime.now()
    current = current.replace(year=2001, month=1, day=1)
    start_time = datetime.datetime.strptime(f'01/01/01 {start_time}', '%m/%d/%y %H:%M:%S')
    end_time = datetime.datetime.strptime(f'01/01/01 {end_time}', "%m/%d/%y %H:%M:%S")

    if DEBUG:
        print(start_time <= current <= end_time)
    
    while not start_time <= current <= end_time:
        current = datetime.datetime.now()
        current = current.replace(year=2001, month=1, day=1)
        if DEBUG:
            print("waiting for hours of operation",start_time - current)
        time.sleep(1)

    if DEBUG:
        print('in time range... ')

    return True


@app.command()
def visit_page(url:str, start_offset:int=0, repeat_every:int=0, hours_of_operation:List[str]=None, start_jitter:int=0, repeat_jitter:int=0 ) -> bool:
    """visit an arbitrary url. can be configured to repeat"""

    if hours_of_operation:
        in_time_range(hours_of_operation)
    
    if DEBUG:
        print(f'{"-"*40 }\nVisiting {url} in {start_offset} seconds; will repeat every {repeat_every} seconds. 0 means do not repeat')
    
    delay(start_offset, start_jitter)
    
    sess = HTMLSession()
    try:
        if repeat_every > 0:
            while True:
                r = sess.get(url)

                if DEBUG:
                    print(f'visit_page: Got {r.status_code} from {r.url}; sleeping {repeat_every} seconds...')

                delay(repeat_every, repeat_jitter)
                
        else:
            r = sess.get(url)
            print(f'visit_page: Got {r.status_code} from {r.url}; all done...')

        return True
    except BaseException as e:
        print(e)
        return False


@app.command()
def run_command(cmd:str, start_offset:int=0, repeat_every:int=0, hours_of_operation:List[str]=None, start_jitter:int=0, repeat_jitter:int=0) -> bool:
    """run an arbitrary system command. the command should not be interactive or blocking in set to repeat"""

    if hours_of_operation:
        in_time_range(hours_of_operation)

    if DEBUG:
        print(f'{"-"*40 }\nRunning {cmd} in {start_offset } seconds +/- {start_jitter} seconds of jitter; will repeat every {repeat_every} seconds +/- {repeat_jitter} seconds of jitter. 0 means does not repeat')
    
    delay(start_offset, start_jitter)
    
    try:
        if repeat_every > 0:
            while True:
                output = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if DEBUG:
                    print(f'run_command "{cmd}" yields "{output.stdout.read().decode()}"')
                
                delay(repeat_every, repeat_jitter)
        else:
            output = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if DEBUG:
                print(f'run_command "{cmd}" yields "{output.stdout.read().decode()}"')
        return True
    except BaseException as e:
        print(e)
        return False

def _send_email(**kwargs):
    """same keyword args as send_email()"""
    
    context = None
    if kwargs.get('encrypted', False):
        context = ssl.create_default_context()


    with smtplib.SMTP(kwargs.get('smtp_server'), kwargs.get('smtp_port') ) as s:
        
        # s.login(kwargs.get('smtp_user'), kwargs.get('smtp_pass'))

        s.sendmail(kwargs.get('sender'), kwargs.get('recipient_list'), kwargs.get('email_body'))


@app.command()
def send_email(recipient_list:List[str], sender:str, email_subj:str=None, email_body:str="Hello", email_headers:str=None, attachments:List[str]=[], smtp_server:str='localhost', smtp_port:int=1025, smtp_user:str='some@user.com', smtp_pass:str="somepass", encrypted:bool=False, start_offset:int=0, repeat_every:int=0, hours_of_operation:List[str]=None, start_jitter:int=0, repeat_jitter:int=0) -> bool:
    """ONLY PARTIALLY IMPLEMENTED; send a single email to a single recipent address"""
    # test server -> python -m smtpd -c DebuggingServer -n localhost:1025
    # https://realpython.com/python-send-email/
    if hours_of_operation:
        in_time_range(hours_of_operation)

    if DEBUG:
         print(f'sending email to {recipient_list} from {sender}; subject {email_subj}; headers {email_headers}; body {email_body}; via {smtp_server}:{smtp_port} in {start_offset } seconds +/- {start_jitter} seconds of jitter; will repeat every {repeat_every} seconds +/- {repeat_jitter} seconds of jitter. 0 means does not repeat')

    # raise NotImplemented

    delay(start_offset, start_jitter)

    func_params = {
        'recipient_list':         recipient_list, 
        'sender':       sender, 
        'email_subj':       email_subj, 
        'email_body':       email_body, 
        'email_headers':    email_headers, 
        'attachments':      attachments, 
        'smtp_server':      smtp_server, 
        'smtp_port':        smtp_port, 
        'smtp_user':        smtp_user, 
        'smtp_pass':        smtp_pass, 
        'encrypted':        encrypted
    }


    try:
        if repeat_every > 0:
            while True:
                if DEBUG:
                    print(f'send_email: continually sending email to {recipient_list} from {sender}; subject {email_subj}; headers {email_headers}; body {email_body}')

                _send_email(**func_params)
                pass
                delay(repeat_every, repeat_jitter)
        else:
            #one shot
            _send_email(**func_params)
            # print(f'send_email: sending one email to {email_to} from {sender}; subject {email_subj}; headers {email_headers}; body {email_body}')
        return True
    except BaseException as e:
        print(e)
        return False

@app.command()
def random_visit(urls:List[str], start_offset:int=0, repeat_every:int=0, hours_of_operation:List[str]=None, start_jitter:int=0, repeat_jitter:int=0 ) -> bool:
    """randomly visit a list of urls"""
    if hours_of_operation:
        in_time_range(hours_of_operation)

    if DEBUG:
        print(f'{"-"*40 }\nVisiting one of {urls} in {start_offset} seconds; will repeat every {repeat_every} seconds. 0 means do not repeat')
    
    delay(start_offset, start_jitter)

    try:
        if repeat_every > 0: 
            while True:
                url = random.choice(urls)
                print(f'Picking random url: {url}')
                visit_page(url)
                delay(repeat_every, repeat_jitter)
        else:
            url = random.choice(urls)
            print(f'Picking random url: {url}')
            visit_page(url)
        return True
    except BaseException as e:
        print(e)
        return False


@app.command()
def wander(url:str, depth=5, delay=30, start_offset:int=0, repeat_every:int=0, hours_of_operation:List[str]=None, start_jitter:int=0, repeat_jitter:int=0) -> bool:
    """NOT IMPLEMENTED FULLY randomly follow links on a page upto depth links deep with a delay of delay in between
    """
    raise NotImplemented

    if hours_of_operation:
        in_time_range(hours_of_operation)

    delay(start_offset, start_jitter)

    try:
        if repeat_every > 0: 
            while True:
                print(f'Wandering url: {url}')
                visit_page(url)
                delay(repeat_every, repeat_jitter)
        else:
            url = random.choice(urls)
            print(f'Picking random url: {url}')
            visit_page(url)
        return True
    except BaseException as e:
        print(e)
        return False

def load_ops(ops_dir='./ops') -> list:
    print(f'loading operations from {ops_dir}')

    ops = []

    op_files = glob.glob(f'{ops_dir}/*.toml')

    for op_file in op_files:
        with open(op_file) as f:
            obj = toml.loads(f.read())
            ops.append(obj)
    
    print('Loaded', ops)

    return ops

@app.command()
def operate(ops=None):
    """actually fire off the operations defined in the ops.toml files"""

    if ops == None:
        ops = load_ops()
    
    t = threading.Thread(target=beacon)
    t.start()
    console.rule('BEGIN')
    
    for op in ops:
        tasks = op.get('tasks')
        
        for task in tasks:
            # print(task.get('action'))
            kwargs = {
                    'start_offset' : task.get('start_offset',0), 
                    'repeat_every' : task.get('repeat_every',0),
                    'hours_of_operation' : task.get('hours_of_operation', None),
                    'start_jitter' : task.get('start_jitter',0),
                    'repeat_jitter' : task.get('repeat_jitter',0),
                }
            if task.get('action') == 'visit':
                args = (
                    task.get('url'), 
                )
                kwargs.update({
                    
                })

                t = threading.Thread(target=visit_page, args=args, kwargs=kwargs)
                t.start()

            elif task.get('action') == 'run':
                args = (
                    task.get('cmd'), 
                )
                kwargs.update({
                })

                t = threading.Thread(target=run_command, args=args, kwargs=kwargs, daemon=True )
                t.start()

            elif task.get('action') == 'random_visit':
                args = (
                    task.get('urls'), 
                )
                kwargs.update({
                })

                t = threading.Thread(target=random_visit, args=args, kwargs=kwargs)
                t.start()

            elif task.get('action') == 'send_email':
                args = (
                    task.get('email_to'),
                    task.get('sender'),
                )
                kwargs.update({
                    'email_subj' : task.get('email_subj'), 
                    'email_body' : task.get('email_body'), 
                    'email_headers' : task.get('email_headers'), 
                    'start_offset' : task.get('start_offset',0), 
                    'repeat_every' : task.get('repeat_every',0) 
                })

                t = threading.Thread(target=visit_page, args=args, kwargs=kwargs, daemon=True )
                t.start()


@app.command()
def newop(files:List[Path]):
    """TESTING load an opfile from an arbitrary path."""
    ops = []
    for file in files:
        with open(file) as f:
            obj = toml.loads(f.read())
            ops.append(obj)
    
    operate(ops)


if __name__ == '__main__':
    

    app()
