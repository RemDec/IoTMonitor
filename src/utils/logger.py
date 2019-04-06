from sys import stdout
from datetime import datetime

class Logger():

    def __init__(self, output=None):
        self.output = stdout if output is None else output
        self.curr_buffer = ""
        self.max_length = 1000

    def log(self, msg, level=0, suffix=""):
        self.output.write("[" + str(level) + "] " + suffix + msg + '\n')
        if len(self.curr_buffer) + len(msg) > self.max_length:
            self.write_logfile()
            self.curr_buffer = ""
        self.curr_buffer += msg

    def write_logfile(self):
        name = datetime.now().strftime('log_%H_%M_%d_%m_%Y.log')
        with open(name, 'w') as fd:
            fd.write(self.curr_buffer)

    def __str__(self):
        return "Logger current state :\n" + "\tBuffer :\n" + self.curr_buffer


if __name__ == '__main__':
    logger = Logger()
    logger.log("A message totally arbitrary")
    print(logger)
    logger.write_logfile()
