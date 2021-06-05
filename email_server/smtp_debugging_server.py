#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# SPDX-License-Identifier: MIT
# https://github.com/FelixSchwarz/pymta/blob/master/examples/debugging_server.py

# python smtp_debugging_server.py localhost 1025
# ./casper_agent.py send-email fake@fake.com user1@user1.com sender@sender.com
#
# yields
# ---------- MESSAGE FOLLOWS ----------
# FROM:   sender@sender.com
# TO:     ['fake@fake.com', 'user1@user1.com']
# MESSAGE:
# Hello
# ------------ END MESSAGE ------------


"""This module contains an equivalent of Python's DebuggingServer which just
prints all received messages to STDOUT and discards them afterwards."""

import os
import sys
import diskcache as dc
import time
from pymta import PythonMTA, IMessageDeliverer

import email_db as db

MX_DOMAINS = [
    'test.com',
    'mail.com',
    'mail.mil',
    'b.com'
]

print('accept messages for ', MX_DOMAINS)
# USERS = dc.Cache('maildb')


def in_domains(recipient):
    for dom in MX_DOMAINS:
        if recipient.lower().endswith(dom):
            return True
    return False

class STDOUTDeliverer(IMessageDeliverer):
    def new_message_accepted(self, msg):
        print('recipients', msg.smtp_to)
        
        our_users = [ r for r in msg.smtp_to if r.split('@')[1].lower().strip() in MX_DOMAINS ]
        
        print(f'our users {our_users}')
        
        if len(our_users) > 0:
            email_dump = ''.join([
                    "---------- MESSAGE FOLLOWS ----------\n",
                    f"FROM:   {msg.smtp_from}\n",
                    f"TO:     {msg.smtp_to}\n",
                    f"MESSAGE:\n{msg.msg_data}\n",
                    "------------ END MESSAGE ------------\n",
                ] 
            ).encode()
            print(email_dump)

            for user in our_users:
                with db.db_session:
                    db_user = db.Account.get(username=user)
                    if db_user == None:
                        db_user = db.Account(username=user, password='pass', domain='test.com')
                    db_msg = db.Message(msg_from=msg.smtp_from, msg_to=repr(msg.smtp_to), msg_body=msg.msg_data, account=db_user)

                # print('user', user)
                # user = user.split('@')[0]
                # user = USERS.get(user)
                # if user == None:

                #     USERS.set(user, {
                #         'password': 'pass',
                #         'messages': [msg,]
                #         } 
                #     )
                # else:
                #     USERS[user]['messages'].append(msg)



        else:
            print(f'msg to {msg.smtp_to} not added to db; not in our domain; forwarding to another server... ')

def list_get(data, index, default=None):
    if len(data) <= index:
        return default
    return data[index]


def print_usage():
    cmd_name = list_get(sys.argv, 0, default=os.path.basename(__file__))
    print("Usage: %s [host] [port]" % cmd_name)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        # sys.exit(0)

    host = list_get(sys.argv, 1, default="localhost")
    port = int(list_get(sys.argv, 2, default=1025))

    server = PythonMTA(host, port, STDOUTDeliverer)
    try:
        print(f"Running on {host}:{port}")
        server.serve_forever()
    except KeyboardInterrupt:
        pass
