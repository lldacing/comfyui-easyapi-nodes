import sys

from datetime import datetime as dt

from server import PromptServer

old_stdout = sys.stdout
old_stderr = sys.stderr


class StdTimeFilter:
    def __init__(self, is_stdout):
        self.is_stdout = is_stdout
        self.newline = True
        self.encoding = "utf-8"

    def write(self, message):
        if message == '\n':
            if self.is_stdout:
                old_stdout.write(message)
                old_stdout.flush()
            else:
                old_stderr.write(message)
                old_stderr.flush()
            self.newline = True
        elif self.newline:
            if self.is_stdout:
                old_stdout.write('%s %s' % (str(dt.now()), message))
            else:
                old_stderr.write('%s %s' % (str(dt.now()), message))
            self.newline = False
        else:
            if self.is_stdout:
                old_stdout.write(message)
            else:
                old_stderr.write(message)

    def flush(self):
        if self.is_stdout:
            old_stdout.flush()
        else:
            old_stderr.flush()

    def isatty(self):
        return sys.__stdout__.isatty()


def socket_wrap(func):
    def wrap_func(event, data, sid=None):
        if event == "executed" or event == "executing":
            print("send message begin, type={}, node={}".format(event, data['node']))
        else:
            print("send message begin, {}".format(event))
        func(event, data, sid)
        print("send message end, {}".format(event))
    return wrap_func


def log_wrap():
    sys.stdout = StdTimeFilter(True)
    sys.stderr = StdTimeFilter(False)
    # old_send_sync = PromptServer.instance.send_sync
    # PromptServer.instance.send_sync = socket_wrap(old_send_sync)
