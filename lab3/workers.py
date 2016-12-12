import Queue
import random
import subprocess
import threading

# number to send to each vessel
NB_MESSAGE_PER_VESSEL = 20

# the seattle port number
DEFAULT_PORT = 63159

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
            args = ['curl', '--silent', '-d', 'entry=' + str(i) + '_from_' + self.target_ip, '-X', 'POST', self.url]

            res = subprocess.Popen(args=args, stdout=subprocess.PIPE)
            output, _ = res.communicate()
            if res.returncode == 0:
                output = output.strip().split('_')
                entry_id = output[0]
                entry_creator_ip = output[1]

                if self.delete_queue is not None:
                    # print "Adding entry %d_%s in the queue" % (int(entry_id), entry_creator_ip)
                    self.delete_queue.put((entry_id, entry_creator_ip))


class DeleteThread(threading.Thread):
    """
    Thread used to delete multiple message
    """

    def __init__(self, target_ip, port_number, delete_queue=None):
        super(DeleteThread, self).__init__()
        self.delete_queue = delete_queue
        self.port_number = port_number
        self.target_ip = target_ip
        self.url = "http://{0}:{1}/entries".format(self.target_ip, self.port_number)

    def run(self):
        global delete_counter

        while delete_counter < max_delete:
            try:
                entry_id, entry_creator_ip = self.delete_queue.get_nowait()
                print "Deleting the entry : %d_%s by %s" % (int(entry_id), entry_creator_ip, self.target_ip)

                args = ['curl', '--silent', '-d', 'delete=1', '-d', 'creator_ip=' + entry_creator_ip, '-X', 'POST',
                        self.url + "/" + str(entry_id)]

                subprocess.Popen(args=args, stdout=subprocess.PIPE)

                delete_counter_lock.acquire()

                delete_counter += 1

                # print 'Counter :', delete_counter

                delete_counter_lock.release()

                self.delete_queue.task_done()
            except Queue.Empty:
                pass


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

    delete_threads = []
    # launch delete thread
    for vessel_ip in reversed(neighbortlist):
        delete_thread = DeleteThread(vessel_ip, DEFAULT_PORT, q)
        delete_thread.start()
