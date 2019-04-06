from threading import Thread
from time import sleep


def has_method(obj, name):
    return callable(getattr(obj, name, None))

class TimerThread(Thread):

    def __init__(self, t=1):
        Thread.__init__(self)
        self.t = t
        self.stopped = True
        self.subs = []

    def launch(self, auto_start=True):
        self.stopped = False
        if auto_start:
            super().start()

    def stop(self):
        self.stopped = True

    def subscribe(self, obj):
        if has_method(obj, 'decr') and has_method(obj, 'is_decrementable'):
            self.subs.append(obj)
        else:
            print("Impossible subscribe,", repr(obj), "should implement decr() and is_decrementable()")

    def unsub(self, obj):
        try:
            self.obj.remove(obj)
        except ValueError:
            pass

    def decr_all(self):
        for o in self.subs:
            if o.is_decrementable():
                o.decr()

    def run(self):
        while not self.stopped:
            sleep(self.t)
            self.decr_all()

    def str(self):
        return "Timer with " + len(self.subs) + " subscribed objects:" + str(self.subs)


class PrototypeSubscriber():

    def __init__(self):
        self.expiration = 5
        self.alive = True

    def is_decrementable(self):
        return self.alive

    def decr(self):
        print("[DumbSubs]Decrement function call")
        if self.expiration <=0:
            from threading import current_thread
            print("[DumbSubs]I died in the thread", current_thread())
            self.alive = False

        elif self.alive:
            self.expiration -= 1

if __name__ == '__main__':
    import threading as thr
    timer = TimerThread()
    obj = PrototypeSubscriber()
    timer.subscribe(obj)
    timer.launch()
    print("Timer started,", thr.active_count(), "threads currently : timer", timer, "and main :", thr.current_thread())
