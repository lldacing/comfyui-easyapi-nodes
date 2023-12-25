import sys

from datetime import datetime as dt

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
            else:
                old_stderr.write(message)
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


def log_wrap():
    sys.stdout = StdTimeFilter(True)
    sys.stderr = StdTimeFilter(False)
