#!/usr/bin/env python3

# https://www.vircom.com/blog/quick-guide-of-pop3-command-line-to-type-in-telnet/
# https://electrictoolbox.com/pop3-commands/ for how pop is supposed to work...
from pony.orm.core import db_decorator, get
from rich import print
import sys
import socketserver
# import glob
# import toml

import os

import diskcache as dc

import email_db as db


# EMAILS = dict()

# USERS = toml.load("email_user_accounts.toml")

# USERS = {
#     "shyft":    "pass",
#     "test":     "test"
# }

# USERS = dc.Cache("maildb")


# mail_store_path = './mail_store'
# os.mkdir(mail_store_path)

# USERS.set('shyft', {
#         'password': 'pass',
#         'messages': [
#             'json data here',
#             'another json message'
#         ]
#     }
# )

# keys are users
# vals are lists of messages

@db.db_session
def get_user(username):
    acct = db.Account.get(username=username)
    if acct != None: 
        return acct
    return False

@db.db_session
def auth_user(username, password):
    res= db.Account.get(username=username, password=password)
    if res != None:
        return True
    return False

@db.db_session
def format_msg(m_id):
    m = db.Message.get(id=m_id)
    if m != None:
        return f'''
msg id:         {m.id}
msg timestamp:  {m.timestamp}
msg from:       {m.msg_from}
msg to:         {m.msg_to}
msg subject:    {m.msg_subj}
msg body:
{m.msg_body}
'''
    return f'invalid id {m_id}'

@db.db_session
def stat_msg(username):
    ret = []
    messages = db.select(m for m in db.Message if username in m.msg_to)
    for m in messages:
        ret.append((m.id, len(m.msg_body)))
    # return ''.join(ret)
    return ret

@db.db_session
def summary_msg(m_id):
    m = db.Message.get(id=m_id)
    return f'\n---\n{m.id}|{m.timestamp}|{m.msg_from}|{m.msg_to}|{m.msg_subj}|{m.msg_body}'
    # return f'{m.id} {len(m.msg_body)}'

@db.db_session
def get_messages(username):
    ret = []
    messages = db.select(m for m in db.Message if username in m.msg_to)
    for m in messages:
        ret.append(summary_msg(m.id))
    # return ''.join(ret)
    return ret
    # message_files = glob.glob(f'{mail_store_path}/{username}/*.mail')

    # messages = []
    # for file in message_files:
    #     with open(file) as f:
    #         messages.append(f.read())


class MailHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.request.sendall(f"+OK POP3 maily server v13.37 ready\n\n".encode())
        self.user = b""
        self.logged_in = False
        self.messages = list()

        while True:
            try:
                raw = self.request.recv(1024).decode()

                self.data = raw.strip().split(" ")

                # breakpoint()
                # self.data = self.data.decode()
                print(f"{self.client_address[0]} sent: {self.data}")

                cmd = self.data[0]
                payload = "".join(self.data[1:])
                # print(f"payload : {payload}")

                if cmd.lower() == "user":
                    self.logged_in == False  # remove this line to be a ctf challenge. read other user emails...
                    if get_user(payload):
                        self.user = payload
                        self.request.sendall(
                            b"+OK Username accepted, password please\n"
                        )
                    else:
                        self.request.sendall(b"-ERR invalid username\n")

                elif cmd.lower() == "pass":
                    print(f'login attempt for user {self.user} with password {payload}')
                    if auth_user(self.user, payload):
                        self.logged_in = True
                        msg = b"+OK password accepted\n"
                        print(f"user {self.user} {msg}")
                        get_messages(self.user)
                        self.request.sendall(msg)

                elif cmd.lower() == "stat":
                    msgs = stat_msg(self.user)
                    self.messages = msgs
                    status = f"logged in:{self.logged_in}\nuser: {self.user}\n"
                    print(status)
                    ret_msg = f"+OK {len(msgs)} {sum([len(m) for m in msgs])}\n".encode()
                    # ret_msg = "+OK 1 1337\n".encode()
                    print(ret_msg)
                    self.request.sendall(ret_msg)

                elif cmd.lower() == "list":
                    if self.logged_in == True:
                        self.messages = ''.join(get_messages(self.user))
                       
                        resp = f"+OK {len(self.messages)} messages\n"
                        for msg in stat_msg(self.user):
                            resp += f"{msg[0]} {msg[1]}\n"
                        # resp += '\n'.join(stat_msg(self.user))
                        resp += ".\n"
                        self.request.sendall(resp.encode())
                    else:
                        self.request.sendall(b"-ERR Must be logged in..\n")

                elif cmd.lower() == "retr":
                    if self.logged_in == True:
                        payload = int(payload)
                        msg = '' 
                        with db.db_session:
                            msg = db.Message.get(id=payload)
                            if msg != None:
                                msg = format_msg(msg.id)
                        if payload >= 0 and payload <= len(self.messages) and msg != None:
                        
                            self.request.sendall(
                                f"+OK\n---BEGIN_MSG---\n{msg}\n---END_MSG---\n.\n".encode()
                            )
                        else:
                            pass  # invalid index
                    else:
                        self.request.sendall(b"-ERR Must be logged in..\n")

                elif cmd.lower() == "top":
                    if self.logged_in == True:
                        if int(payload) >= 0 and int(payload) <= len(self.messages):
                            msg = self.messages[int(payload) - 1]
                            self.request.sendall(
                                f"+OK\n---BEGIN_MSG---\n{msg[:100]}\n---END_MSG---\n.\n".encode()
                            )
                        else:
                            pass  # invalid index
                    else:
                        self.request.sendall(b"-ERR Must be logged in..\n")

                elif cmd.lower() == "dele":
                    if self.logged_in == True:
                        m_id = int(payload)
                        with db.db_session:
                            msg = db.Message.get(id=m_id)
                            if msg != None:
                            # msg = self.messages.pop(int(payload) - 1)
                                msg_str = format_msg(m_id)
                                self.request.sendall(f"+OK Deleted msg {m_id}\n---BEGIN_MSG---\n{msg_str}\n---END_MSG---\n.\n".encode())
                                msg.delete()
                                print(f'deleted msg id {m_id}')
                    else:
                        self.request.sendall(b"-ERR Must be logged in..\n")
                elif cmd.lower() == "quit":
                    self.request.sendall(b"+OK BYE\n")
                    break
                else:
                    self.request.sendall(b"-ERR Unknown command... try again\n")

            except BrokenPipeError as e:
                return
            except BaseException as e:
                print(e)


if __name__ == "__main__":
    HOST, PORT = "localhost", 1110

    # Create the server, binding to localhost on port 9999
    with socketserver.TCPServer((HOST, PORT), MailHandler) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        print("Running on", HOST, PORT)
        try:
            server.allow_reuse_address = True
            server.serve_forever()
        except KeyboardInterrupt as e:
            print("quitting... ")
            server.server_close()
            sys.exit(0)
