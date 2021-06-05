#!/usr/bin/env python3

from rich.console import Console

console = Console()
original_print = print
print = console.log  # hijack the print

from requests_html import HTMLSession
import toml
import typer
import faker

import datetime
import subprocess
import time
from datetime import timedelta
import glob
import random
import multiprocessing
import threading

# import shlex
import uuid
import json
import socket
import smtplib
import poplib
import ssl
import sys
from typing import List
from pathlib import Path


app = typer.Typer()  # for cli operations


fake = faker.Faker()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("1.1.1.1", 80))
AGENT_IP = s.getsockname()[0]
s.close()

AGENT_UUID = uuid.uuid3(
    uuid.NAMESPACE_DNS, str(uuid.getnode())
).hex  # based on mac address
AGENT_PLATFORM = sys.platform
AGENT_TAGS = []

DEBUG = True

BEACON = True  # disable the beacon with ./casper_client --no-only-beacon
ONLY_BEACON = False
C2_BEACON_SERVER = "http://localhost:5000"
C2_BEACON_ENDPOINT = (
    "/beacon"  # for beaconing stats about operations to casper_server.py
)
IS_BEACONING = False  # this will be used to signal whether or not we are beaconing.
LAST_ACTION = ""  # for the beacon....
LAST_RESULT = ""  # basic results.


OPS_DIR = "./ops"
OPS = []


@app.callback()
def load_config(
    config_file: Path = Path("config.toml"),
    debug: bool = True,
):
    global AGENT_UUID
    global AGENT_TAGS
    global DEBUG
    global BEACON
    global ONLY_BEACON
    global C2_BEACON_SERVER
    global C2_BEACON_ENDPOINT
    global OPS_DIR

    try:
        config = toml.loads(open(config_file).read())

        AGENT_UUID = config.get(
            "AGENT_UUID", uuid.uuid3(uuid.NAMESPACE_DNS, str(uuid.getnode())).hex
        )
        AGENT_TAGS = config.get("AGENT_TAGS", [])

        DEBUG = config.get("DEBUG", True)

        BEACON = config.get("BEACON", True)
        C2_BEACON_SERVER = config.get("C2_BEACON_SERVER", "http://localhost:5000")
        C2_BEACON_ENDPOINT = config.get("C2_BEACON_ENDPOINT", "/beacon")

        OPS_DIR = config.get("OPS_DIR", "./ops")

    except BaseException as e:
        print(e)
        print("failed to load config... ")
        sys.exit()


def _jitter(jitter_amount=0) -> int:
    if jitter_amount == 0:
        return 0
    return random.randint(jitter_amount * -1, jitter_amount)


def delay(base_time, jitter_amount):
    if jitter_amount != 0:
        jitter_amount = _jitter(jitter_amount=jitter_amount)

    time.sleep(abs(base_time + jitter_amount))


@app.command()
def get_uuid():
    """this returns the uuid of agent on THIS computer (useful for targeting ops.)
    derived from uuid.uuid3(uuid.NAMESPACE_DNS, str(uuid.getnode())).hex # based on mac address"""
    original_print(AGENT_UUID)


def beacon(interval: int = 5, jitter_amount: int = 0):
    """only send beacons"""
    global LAST_ACTION
    global IS_BEACONING

    if BEACON == False or IS_BEACONING == True:
        return

    IS_BEACONING = True

    while True:
        BEACON_PAYLOAD = {
            "uuid": AGENT_UUID,
            "time": str(datetime.datetime.now()),
            "ip": AGENT_IP,
            "platform": AGENT_PLATFORM,
            "tags": AGENT_TAGS,
            "last_action": LAST_ACTION,
        }
        if DEBUG:
            print(f"beacon payload: {BEACON_PAYLOAD}")
        try:
            sess = HTMLSession()

            r = sess.post(
                f"{C2_BEACON_SERVER}{C2_BEACON_ENDPOINT}", json=BEACON_PAYLOAD
            )

            new_ops = json.loads(r.text).get("OPS")

            if DEBUG:
                print(f"beacon: {r}; retrieved new operations {new_ops}")

            if ONLY_BEACON == False and len(new_ops) > 0:
                if DEBUG:
                    print("Executing new operations... ")
                operate(ops=new_ops, new_ops=True)

        except BaseException as e:
            print(f"Error beaconing: {e}")

        

        # time.sleep(interval + _jitter(jitter_amount=jitter_amount))
        delay(interval, jitter_amount)


def in_time_range(hours_of_operation: List[str], msg="") -> bool:
    if hours_of_operation == None or hours_of_operation == []:
        return True

    start_time = hours_of_operation[0]
    end_time = hours_of_operation[1]

    current = datetime.datetime.now()
    current = current.replace(year=2001, month=1, day=1)
    start_time = datetime.datetime.strptime(
        f"01/01/01 {start_time}", "%m/%d/%y %H:%M:%S"
    )
    end_time = datetime.datetime.strptime(f"01/01/01 {end_time}", "%m/%d/%y %H:%M:%S")

    while not start_time <= current <= end_time:
        current = datetime.datetime.now()
        current = current.replace(year=2001, month=1, day=1)
        delta = start_time - current
        if DEBUG:
            print(msg, "waiting for hours of operation", delta)
        if delta < timedelta(seconds=30):
            time.sleep(1)
        else:
            print("sleeping 10 seconds...")
            time.sleep(10)

    if DEBUG:
        print(msg, "in time range")

    return True


def is_target(
    target_ids: List[str] = [],
    target_platforms: List[str] = [],
    target_tags: List[str] = [],
):
    if target_ids == ["all"]:  # this will come from the call to is_target in operate function...
        return True

    if AGENT_UUID in target_ids:
        print("is a target id")
        return True
    elif AGENT_PLATFORM in target_platforms:
        print("is a target platform")
        return True
    for tag in AGENT_TAGS:
        if tag in target_tags:
            print("has a target tag")
            return True

    # print("not a target for this op")
    return False


@app.command()
def visit_page(
    url: str,
    start_offset: int = 0,
    repeat_every: int = 0,
    hours_of_operation: List[str] = None,
    start_jitter: int = 0,
    repeat_jitter: int = 0,
) -> bool:
    """visit an arbitrary url. can be configured to repeat"""
    if hours_of_operation:
        in_time_range(hours_of_operation, msg=f"visit_page {url}")

    if DEBUG:
        print(
            f'{"-"*40 }\nVisiting {url} in {start_offset} seconds; will repeat every {repeat_every} +/- {repeat_jitter} seconds. 0 means do not repeat'
        )

    delay(start_offset, start_jitter)

    sess = HTMLSession()
    global LAST_ACTION
    try:
        if repeat_every > 0:
            while True:
                resp = sess.get(url)
                resp.html.render()
                action = f"visit_page: Got {resp.status_code} from {resp.url}; sleeping {repeat_every} +/- {repeat_jitter} seconds..."

                if DEBUG:
                    print(action)

                LAST_ACTION = action

                delay(repeat_every, repeat_jitter)

        else:
            resp = sess.get(url)
            action = f"visit_page: Got {resp.status_code} from {resp.url}; all done..."
            print(action)

            LAST_ACTION = action

        return True
    except BaseException as e:
        print(e)
        return False


@app.command()
def run_command(
    cmd: str,
    start_offset: int = 0,
    repeat_every: int = 0,
    hours_of_operation: List[str] = None,
    start_jitter: int = 0,
    repeat_jitter: int = 0,
) -> bool:
    """run an arbitrary system command. the command should not be interactive or blocking in set to repeat"""

    if hours_of_operation:
        in_time_range(hours_of_operation, msg=f"run_command {cmd}")

    if DEBUG:
        print(
            f'{"-"*40 }\nRunning {cmd} in {start_offset } seconds +/- {start_jitter} seconds of jitter; will repeat every {repeat_every} seconds +/- {repeat_jitter} seconds of jitter. 0 means does not repeat'
        )

    delay(start_offset, start_jitter)
    global LAST_ACTION
    try:
        if repeat_every > 0:
            while True:
                output = subprocess.Popen(
                    cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                action = f'run_command "{cmd}" yields "{output.stdout.read().decode()}"'

                if DEBUG:
                    print(action)

                LAST_ACTION = action

                delay(repeat_every, repeat_jitter)
        else:
            output = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            action = f'run_command "{cmd}" yields "{output.stdout.read().decode()}"'

            if DEBUG:
                print(action)

            LAST_ACTION = action

        return True
    except BaseException as e:
        print(e)
        return False


def _send_email(**kwargs):
    """same keyword args as send_email()"""

    context = None
    if kwargs.get("encrypted", False):
        context = ssl.create_default_context()

    with smtplib.SMTP(kwargs.get("smtp_server",'localhost'), kwargs.get("smtp_port",1025)) as s:

        # s.login(kwargs.get('smtp_user'), kwargs.get('smtp_pass'))

        s.sendmail(
            kwargs.get("sender",''), kwargs.get("recipient_list",[]), kwargs.get("email_body",'')
        )


@app.command()
def send_email(
    recipient_list: List[str],
    sender: str = None,
    email_subj: str = None,
    email_body: str = None,
    email_headers: str = None,
    attachments: List[str] = [],
    smtp_server: str = "localhost",
    smtp_port: int = 1025,
    smtp_user: str = "some@user.com",
    smtp_pass: str = "somepass",
    encrypted: bool = False,
    start_offset: int = 0,
    repeat_every: int = 0,
    hours_of_operation: List[str] = None,
    start_jitter: int = 0,
    repeat_jitter: int = 0,
) -> bool:
    """ONLY PARTIALLY IMPLEMENTED; send an email to multiple recipent addresses
    test server -> python -m smtpd -c DebuggingServer -n localhost:1025
    https://realpython.com/python-send-email/
    """

    if sender == None:
        sender = fake.email()

    if email_body == None:
        email_body = " ".join(fake.sentences(random.randint(1, 10)))

    if email_subj == None:
        email_subj = " ".join(fake.sentence(1))

    if hours_of_operation:
        in_time_range(
            hours_of_operation,
            msg=f"send_email to {recipient_list} with subject {email_subj}",
        )

    if DEBUG:
        print(
            f"sending email to {recipient_list} from {sender}; subject {email_subj}; headers {email_headers}; body {email_body}; via {smtp_server}:{smtp_port} in {start_offset } seconds +/- {start_jitter} seconds of jitter; will repeat every {repeat_every} seconds +/- {repeat_jitter} seconds of jitter. 0 means does not repeat"
        )

    delay(start_offset, start_jitter)

    func_params = {
        "recipient_list": recipient_list,
        "sender": sender,
        "email_subj": email_subj,
        "email_body": email_body,
        "email_headers": email_headers,
        "attachments": attachments,
        "smtp_server": smtp_server,
        "smtp_port": smtp_port,
        "smtp_user": smtp_user,
        "smtp_pass": smtp_pass,
        "encrypted": encrypted,
    }

    global LAST_ACTION
    try:
        if repeat_every > 0:
            while True:
                
                sender = fake.email()
                email_body = " ".join(fake.sentences(random.randint(1, 10)))
                email_subj = " ".join(fake.sentence(1))
                
                func_params = {
                        "recipient_list": recipient_list,
                        "sender": sender,
                        "email_subj": email_subj,
                        "email_body": email_body,
                        "email_headers": email_headers,
                        "attachments": attachments,
                        "smtp_server": smtp_server,
                        "smtp_port": smtp_port,
                        "smtp_user": smtp_user,
                        "smtp_pass": smtp_pass,
                        "encrypted": encrypted,
                    }

                action = f"send_email: continually sending email to {recipient_list} from {sender}; subject {email_subj}; headers {email_headers}; body {email_body}"

                _send_email(**func_params)

                if DEBUG:
                    print(action)

                LAST_ACTION = action

                delay(repeat_every, repeat_jitter)
        else:
            # one shot
            action = f"send_email: sending an email to {recipient_list} from {sender}; subject {email_subj}; headers {email_headers}; body {email_body}"

            _send_email(**func_params)

            LAST_ACTION = action

        return True
    except BaseException as e:
        print(e)
        if smtp_server == 'localhost' and smtp_port == 1025:
            print('''It looks like you are running the default smtp server settings. 
try running "cd email_server && python smtp_debugging_server.py" or "python -m smtpd -c DebuggingServer -n localhost:1025" both operate on 1025 for MTA features. 
You'll probably want to run the POP3 server pop3_debugging_server.py in the same dir. operates on port 1110 by default for MDA features
''')
        return False


@app.command()
def random_visit(
    urls: List[str],
    start_offset: int = 0,
    repeat_every: int = 0,
    hours_of_operation: List[str] = None,
    start_jitter: int = 0,
    repeat_jitter: int = 0,
) -> bool:
    """randomly visit a list of urls"""
    if hours_of_operation:
        in_time_range(hours_of_operation, msg=f"random_visit unknown url... ")

    if DEBUG:
        print(
            f'{"-"*40 }\nVisiting one of {urls} in {start_offset} seconds; will repeat every {repeat_every} seconds. 0 means do not repeat'
        )

    delay(start_offset, start_jitter)

    try:
        if repeat_every > 0:
            while True:
                url = random.choice(urls)
                print(f"Picking random url: {url}")
                visit_page(url)
                delay(repeat_every, repeat_jitter)
        else:
            url = random.choice(urls)
            print(f"Picking random url: {url}")
            visit_page(url)
        return True
    except BaseException as e:
        print(e)
        return False


def _wander(url, dwell=30, depth=5, current_depth=0):
    if current_depth > depth:
        return False
    if DEBUG:
        print(f'current depth {current_depth}')

    sess = HTMLSession()
    # print(f'visiting {url}')
    resp = sess.get(url, verify=False)
    # breakpoint()
    resp.html.render()
    urls = list(resp.html.absolute_links)
    
    if len(urls) == 0:
        return True

    next_url = random.choice(urls)
    if DEBUG:
        print(f"available urls: {urls}")
        print("next_url is", next_url)

    delay(dwell, 1)

    _wander(next_url, dwell=dwell, depth=depth, current_depth=current_depth + 1)
    return True


@app.command()
def wander(
    url: str,
    wander_depth: int = 5,
    current_depth: int = 0,
    wander_dwell: int = 30,
    start_offset: int = 0,
    repeat_every: int = 0,
    hours_of_operation: List[str] = None,
    start_jitter: int = 0,
    repeat_jitter: int = 0,
) -> bool:
    """randomly follow links on a page upto depth links deep with a delay of delay in between"""

    if hours_of_operation:
        in_time_range(hours_of_operation, msg=f"wandering {url}")

    delay(start_offset, start_jitter)

    try:
        if repeat_every > 0:
            while True:
                print(f"Wandering url: {url}")
                _wander(url, dwell=wander_dwell, depth=wander_depth, current_depth=current_depth)

                delay(repeat_every, repeat_jitter)
        else:

            print(f"Wandering url: {url}")
            _wander(url, dwell=wander_dwell, depth=wander_depth, current_depth=current_depth)
        return True
    except BaseException as e:
        print(e)
        return False


def load_ops(ops_dir=OPS_DIR, op_filter="*") -> list:
    print(f"loading operations from {ops_dir}")

    ops = []

    op_files = glob.glob(f"{ops_dir}/{op_filter}.toml")

    for op_file in op_files:
        with open(op_file) as f:
            obj = toml.loads(f.read())
            ops.append(obj)

    # print("Loaded", ops)

    return ops


@app.command()
def operate(
    ops=[],
    no_ops: bool = False,
    op_filter="*",
    new_ops=False,
    ops_dir: Path = Path("./ops"),
    beacon_only: bool = False,
    tags: List[str] = [],
    
):
    """actually fire off the operations defined in the ops.toml files"""

    if ops == [] and new_ops == False:
        ops = load_ops(ops_dir=ops_dir, op_filter=op_filter)
    if no_ops == True:
        ops = []

    if tags != []:
        global AGENT_TAGS
        AGENT_TAGS = tags

    if IS_BEACONING == False:
        t = threading.Thread(target=beacon)
        t.start()
        if beacon_only:
            return
        console.rule("BEGIN")

    for op in ops:
        tasks = op.get("tasks")

        for task in tasks:

            if (
                is_target(
                    target_ids=task.get("target_uuids", []),
                    target_platforms=task.get("target_platforms", []),
                    target_tags=task.get("target_tags", []),
                )
                == False
            ):
                # I am not a valid target for this tasking... move on to the next tasking...
                print("I am not a valid target")
                continue

            print("I am a valid target")

            # all of the common args for tasks are here
            kwargs = {
                "start_offset": task.get("start_offset", 0),
                "repeat_every": task.get("repeat_every", 0),
                "hours_of_operation": task.get("hours_of_operation", None),
                "start_jitter": task.get("start_jitter", 0),
                "repeat_jitter": task.get("repeat_jitter", 0),
            }


            if task.get("action") == "visit":
                args = (task.get("url"),)
                kwargs.update({})

                t = threading.Thread(target=visit_page, args=args, kwargs=kwargs, daemon=True)
                t.start()
                

            elif task.get("action") == "run":
                args = (task.get("cmd"),)
                kwargs.update({})

                t = threading.Thread(
                    target=run_command, args=args, kwargs=kwargs, daemon=True
                )
                t.start()

            elif task.get("action") == "random_visit":
                args = (task.get("urls"),)
                kwargs.update({})

                t = threading.Thread(target=random_visit, args=args, kwargs=kwargs, daemon=True)
                t.start()
            elif task.get("action") == "wander":
                args = (task.get("starting_url"),)
                kwargs.update({
                    'wander_dwell': task.get('wander_dwell', 30),
                    'wander_depth': task.get('wander_depth', 0),
                    'wander_jitter': task.get('wander_jitter', 0),
                })

                t = threading.Thread(target=random_visit, args=args, kwargs=kwargs, daemon=True)
                t.start()
            elif task.get("action") == "send_email":
                args = (
                    task.get("recipient_list",[]),
                    task.get("sender"),
                )
                kwargs.update(
                    {
                        "email_subj": task.get("email_subj"),
                        "email_body": task.get("email_body"),
                        "email_headers": task.get("email_headers"),
                        "start_offset": task.get("start_offset", 0),
                        "repeat_every": task.get("repeat_every", 0),
                    }
                )

                t = threading.Thread(
                    target=send_email, args=args, kwargs=kwargs, daemon=True
                )
                t.start()
    print(f"Done processing {len(ops)} ops...")


@app.command()
def remote_ops(server: str = C2_BEACON_SERVER):
    sess = HTMLSession()
    resp = sess.get(f"{server}/newops")
    print(resp.text)

@app.command()
def flush_ops(server:str = C2_BEACON_SERVER):
    sess = HTMLSession()
    resp = sess.get(f"{server}/flushops")
    print(resp.text)


@app.command()
def push_op(files: List[Path]):
    """TESTING load an opfile from an arbitrary path."""
    ops = []
    for file in files:
        with open(file) as f:
            obj = toml.loads(f.read())
            ops.append(obj)

    sess = HTMLSession()
    resp = sess.post(f"{C2_BEACON_SERVER}/newops", json=ops)

    print(resp.json())


if __name__ == "__main__":
    load_config()
    app()
