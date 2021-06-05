from datetime import datetime
from pony.orm import *


db = Database()
db.bind(provider='sqlite', filename='mail.sqlite', create_db=True)


class Account(db.Entity):
    id = PrimaryKey(int, auto=True)
    username = Optional(str)
    password = Optional(str)
    domain = Optional(str)
    messages = Set('Message')


class Message(db.Entity):
    id = PrimaryKey(int, auto=True)
    timestamp = Optional(datetime, default=lambda: datetime.now())
    msg_from = Optional(str)
    msg_to = Optional(str)
    msg_subj = Optional(str)
    msg_body = Optional(str)
    account = Required(Account)


db.generate_mapping(create_tables=True)
with db_session:
    if Account.get(username='shyft') == None:
        shyft = Account(username='shyft', password='pass')
        test =  Account(username='test', password='pass')
        msg1 = Message(msg_to="shyft@mail.mil", msg_body='msg 1 3easdfasdf', account=shyft)
        msg2 = Message(msg_to="shyft@mail.com",msg_body='msg 2 asldfj9oiwjef', account=shyft)
        msg3 = Message(msg_to="test@mail.mil", msg_body='not for shyft asldfj9oiwjef', account=test)