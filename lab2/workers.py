import Queue
import random
import subprocess
import threading

# number to send to each vessel
NB_MESSAGE_PER_VESSEL = 12

# the seattle port number
DEFAULT_PORT = 63122

NEIGHBORS_FILE_NAME = "neighborlist.txt"

# number of delete messages sent
delete_counter = 0

# lock used to count the number of delete messages sent
delete_counter_lock = threading.Lock()


class PostThread(threading.Thread):
    """
    Thread used to post (add) multiple entries to a vessel
    """

    def __init__(self, target_ip, port_number, nb_messages, delete_queue=None):
        """
        :param nb_messages: number of messages to send to the vessel
        :param target_ip: Ip address of the vessel
        :param port_number: port number of the vessel
        """
        super(PostThread, self).__init__()
        self.delete_queue = delete_queue
        self.port_number = port_number
        self.nb_messages = nb_messages
        self.target_ip = target_ip
        self.url = "http://{0}:{1}/entries".format(self.target_ip, self.port_number)

    def run(self):
        for i in range(self.nb_messages):
            waiting_time = random.randint(1, 3)
            # print "Waiting %d seconds before sending a post to %s... " % (waiting_time, self.url)
            # time.sleep(waiting_time)
            args = ['curl', '--silent', '-d', 'entry=c' + str(i), '-X', 'POST', self.url]
            print "Posting to %s..." % self.target_ip
            subprocess.Popen(args=args, stdout=subprocess.PIPE)


def _read_neighborlist():
    neighbors = []
    with open(NEIGHBORS_FILE_NAME) as f:
        for line in f:
            neighbors.append(line.strip())

    return neighbors


if __name__ == '__main__':
    neighbortlist = _read_neighborlist()

    nb_vessel = len(neighbortlist)
    if nb_vessel == 0:
        print("No vessel on which post entries")
        exit(1)

    global max_delete
    max_delete = NB_MESSAGE_PER_VESSEL * nb_vessel

    # Delete messages queues
    q = Queue.LifoQueue()

    print(
        "Sending {0} messages to each vessels : {1}".format(NB_MESSAGE_PER_VESSEL, neighbortlist))

    # launch post threads
    for vessel_ip in neighbortlist:
        post_thread = PostThread(vessel_ip, DEFAULT_PORT, NB_MESSAGE_PER_VESSEL, q)
        post_thread.start()