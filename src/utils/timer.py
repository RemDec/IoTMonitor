import abc
import logging
from threading import Thread
from time import sleep
from src.utils.misc_fcts import has_method


class TimerThread(Thread):

    def __init__(self, autostart=False, t=1, name="DefaultTimer"):
        Thread.__init__(self)
        self.t = t
        self.stopped = True
        self.name = name
        self.subs = []
        if autostart:
            self.launch()

    def launch(self):
        if self.stopped:
            self.stopped = False
            super().start()
        else:
            logging.getLogger("debug").debug("Trying to relaunch timer when running" + str(self))

    def stop(self):
        self.stopped = True

    def subscribe(self, obj):
        if not obj in self.subs:
            if has_method(obj, 'decr') and has_method(obj, 'is_decrementable'):
                self.subs.append(obj)
            else:
                print("Impossible subscribe,", repr(obj), "should implement decr() and is_decrementable()")

    def unsub(self, obj):
        try:
            self.subs.remove(obj)
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
        logging.getLogger("debug").debug("End of timer running loop" + str(self))

    def start(self):
        # overriding super method to avoid confusion of calling super.start() only (doesn't launch timer correctly)
        self.launch()

    def detail_str(self, level=0):
        state = "stopped" if self.stopped else "running"
        if level == 0:
            return f"{self.name} ({state})"
        elif level == 1:
            return f"{self.name} (timer state : {state}, interval {self.t}s) ~ {len(self.subs)} subscribers"
        else:
            if len(self.subs) == 0:
                return f"Timer {self.name} ({state}) with no subscribed object"
            subs_str = '\n  > ' + '\n  > '.join([f"[{i+1}] {obj}" for i, obj in enumerate(self.subs)])
            return f"{self.name} ({state}) with {len(self.subs)} subscribed objects:{subs_str}"

    def __str__(self):
        return self.detail_str(0)


class TimerInterface(abc.ABC):

    @abc.abstractmethod
    def is_decrementable(self):
        # Bool indicating wether call or not decr() on subscribed object
        pass

    @abc.abstractmethod
    def decr(self):
        # Call done each times Timer triggers (1 sec likely)
        pass


class PrototypeSubscriber(TimerInterface):

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
    import time
    timer = TimerThread()
    obj = PrototypeSubscriber()
    timer.subscribe(obj)
    timer.launch()
    print(f"{timer.name} started, {thr.active_count()} threads currently : timer {timer} and main :{thr.current_thread()}")
    time.sleep(10)
    timer.stop()
