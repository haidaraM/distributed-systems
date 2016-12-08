import Queue
import random
import subprocess
import threading
import time

# number max of messages to send to all the vessels
NB_MAX_MESSAGE = 20

# the seattle port number
DEFAULT_PORT = 63159

NEIGHBORS_FILE_NAME = "neighborlist.txt"


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
            time.sleep(waiting_time)
            args = ['curl', '--silent', '-d', 'entry=curl' + str(i), '-X', 'POST', self.url]

            res = subprocess.Popen(args=args, stdout=subprocess.PIPE)
            output, _ = res.communicate()
            if res.returncode == 0:
                output = output.strip().split('_')
                entry_id = output[0]
                entry_creator_ip = output[1]
                # print "Entry id : ", entry_id, ". Entry creator : ", entry_creator_ip

                if self.delete_queue is not None:
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
        while True:
            time.sleep(random.randint(1, 3))
            entry_id, entry_creator_ip = self.delete_queue.get()
            print "Deleting the entry : %d_%s" % (int(entry_id), entry_creator_ip)

            args = ['curl', '--silent', '-d', 'delete=1', '-d', 'creator_ip=' + entry_creator_ip, '-X', 'POST',
                    self.url + "/" + str(entry_id)]

            subprocess.Popen(args=args, stdout=subprocess.PIPE)

            self.delete_queue.task_done()


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

    nb_message_per_vessel = int(NB_MAX_MESSAGE / nb_vessel)

    # Delete messages queues
    q = Queue.LifoQueue()

    print(
        "Sending {0} messages to each of the {1} vessels : {2}".format(nb_message_per_vessel, nb_vessel, neighbortlist))

    # launch post threads
    for vessel_ip in neighbortlist:
        post_thread = PostThread(vessel_ip, DEFAULT_PORT, nb_message_per_vessel, q)
        post_thread.start()

    # launch deleting thread
    for vessel_ip in reversed(neighbortlist):
        delete_thread = DeleteThread(vessel_ip, DEFAULT_PORT, q)
        delete_thread.setDaemon(True)
        delete_thread.start()

    q.join()
