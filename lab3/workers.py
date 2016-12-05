import random
import subprocess
import threading
import time

# import requests


# number max of messages to send to all the vessels
NB_MAX_MESSAGE = 20

DEFAULT_PORT = 63159

NEIGHBORS_FILE_NAME = "neighborlist.txt"


class PostThread(threading.Thread):
    """
    Thread used to post multiple entries to a vessel
    """

    def __init__(self, target_ip, port_number, nb_messages):
        """
        :param nb_messages: number of messages to send to the vessel
        :param target_ip: Ip address of the vessel
        :param port_number: port number of the vessel
        """
        super(PostThread, self).__init__()
        self.port_number = port_number
        self.nb_messages = nb_messages
        self.target_ip = target_ip
        self.url = "http://{0}:{1}/entries".format(self.target_ip, self.port_number)

    def run(self):
        for i in range(self.nb_messages):
            # trying to simulate network latency
            time.sleep(random.randint(1, 5))
            subprocess.call(['curl', '--silent', '-d', 'entry=curl' + str(i), '-X', 'POST', self.url])
            # parameters = {'entry': 'message {0}'.format(i)}
            # ok = requests.post(self.url, data=parameters)
            # print("Status code : {0} from {1}".format(ok.status_code, self.target_ip))


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

    print("Sending {0} messages to each of the {1} vessels : {2}".format(nb_message_per_vessel, nb_vessel, neighbortlist))
    for vessel_ip in neighbortlist:
        PostThread(vessel_ip, DEFAULT_PORT, nb_message_per_vessel).start()
