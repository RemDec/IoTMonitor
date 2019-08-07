from src.utils.constants import MAX_FEEDBACK_QSIZE


class Feedback:

    def __init__(self, nbr_pull=3, nbr_pass=1):
        self.feedqueue = []
        self.nbr_to_pull = nbr_pull
        self.nbr_to_pass = nbr_pass

    def feed(self, feed_string):
        if not isinstance(feed_string, str):
            feed_string = str(feed_string)
        split_lines = feed_string.split('\n')
        if len(self) + len(split_lines) <= MAX_FEEDBACK_QSIZE:
            self.feedqueue.extend(split_lines)
        else:
            # Queue is full, pop first messages in the queue
            excedent = len(self) + len(split_lines) - MAX_FEEDBACK_QSIZE
            self.pull_feedback(nbr_lines=excedent, nbr_pass=excedent)
            self.feedqueue.extend(split_lines)

    def pull_feedback(self, nbr_lines=None, nbr_pass=None):
        nbr_lines = nbr_lines if nbr_lines is not None else self.nbr_to_pull
        nbr_pass = nbr_pass if nbr_pass is not None else self.nbr_to_pass
        to_return = '\n'.join(self.feedqueue[:nbr_lines])  # First lines to retrieve
        if len(self.feedqueue) > nbr_lines:
            # There are lines yet waiting to be retrieved, then pass the first ones we just retrieved
            self.feedqueue = self.feedqueue[nbr_pass:]
        if len(to_return) > 0:
            if to_return[-1] != '\n':
                return to_return + '\n'
            return to_return
        return ''

    def __len__(self):
        return len(self.feedqueue)

    def detail_str(self, level=2):
        if level < 3:
            return self.pull_feedback(nbr_pass=0)
        s = '+----------------- - -  -   -     -\n'
        pull_range = min(self.nbr_to_pull, len(self))
        s += '\n'.join(["' " + line.strip() for line in self.feedqueue[:pull_range]])
        s += '\n+----------------- - -  -   -     -'
        s += '\n  ' + '\n  '.join(self.feedqueue[pull_range:])
        if level < 5:
            return s
        else:
            header = f"Feedback state : {len(self)} lines waiting, pull {self.nbr_to_pull} and pass {self.nbr_to_pass}" \
                     f" at once\n"
            return header + s
