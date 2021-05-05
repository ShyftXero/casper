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


from pymta import PythonMTA, IMessageDeliverer


class STDOUTDeliverer(IMessageDeliverer):
    def new_message_accepted(self, msg):
        print("---------- MESSAGE FOLLOWS ----------")
        print(f"FROM:   {msg.smtp_from}")
        print(f"TO:     {msg.smtp_to}")
        print(f"MESSAGE:\n{msg.msg_data}")
        print("------------ END MESSAGE ------------")


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
        sys.exit(0)

    host = list_get(sys.argv, 1, default="localhost")
    port = int(list_get(sys.argv, 2, default=1025))

    server = PythonMTA(host, port, STDOUTDeliverer)
    try:
        print(f"Running on {host}:{port}")
        server.serve_forever()
    except KeyboardInterrupt:
        pass
