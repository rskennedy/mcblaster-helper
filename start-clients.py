import subprocess
import time
import argparse
import os

# path to mcblaster EXECUTABLE
MCBLASTER_PATH = os.environ['MCBLASTER_PATH']


class client(object):
    def __init__(self, hostname, port, rate, duration):
        self.port = port
        self.rate = rate
        self.duration = duration
        self.args = [MCBLASTER_PATH, "-d", str(duration), "-t", "1", "-r", str(rate), "-u", str(port), hostname]
        self.process = subprocess.Popen(self.args, stdout=subprocess.PIPE)

    def get_stdout(self):
        output = self.get_output()
        return output[0] if output else None

    def get_stderr(self):
        output = self.get_output()
        return output[1] if output else None

    def get_output(self):
        """
        Attempt to retrieve output from process.
        If the process is not finished, we wait <duration> seconds and try again.
        If it is still not finished, we let the caller know to move on,
        and it should recheck this client at a later time.
        :return: tuple with stdout and stderr
        """
        if self.process.poll() is None:
            time.sleep(self.duration);
            if self.process.poll() is None:
                return None
        return self.process.communicate()


def startclients(hostname, starting_port, rate, n, duration, set_first=True):
    """
    Create n new clients to blast memcached cluster.
    :param hostname:
    :param starting_port: Where to begin incrementing port number.
    :param rate: How many requests per second for each client.
    :param n: Number of ports to blast.
    :return client_list: list of client objects
    """
    client_list = []
    if set_first:
        """
        Make sure to fill each memcached instance with a key before recording GETs. 
        """
        for i in range(n):
            port = starting_port + i
            args = [MCBLASTER_PATH, "-t", "1", "-d", "1", "-w", "5", "-p", str(port), hostname]
            subprocess.check_output(args, stderr=subprocess.STDOUT)
    """
    Create each client object which will create a mcblaster subproc on init.
    """
    for i in range(n):
        port = starting_port + i
        client_list.append(client(hostname, port, rate, duration))
    return client_list


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("server")
    parser.add_argument("starting_port", help="port to begin scanning", type=int)
    parser.add_argument("--rate", help="requests per second", type=int)
    parser.add_argument("--n", help="number of clients to create", type=int)
    parser.add_argument("--duration", help="duration of client in seconds", type=int)

    args = parser.parse_args()
    server = args.server
    starting_port = args.starting_port
    rate = args.rate if args.rate else 1000
    nb_clients = args.n if args.n else 1
    duration = args.duration if args.duration else 2

    clients = startclients(server, starting_port, rate, nb_clients, duration)

    slow_clients = []
    for client in clients:
        stdout = client.get_stdout()
        if stdout is None:
            slow_clients.append(client)
            continue

        print "---------------------------------------"
        print "Client blasted port {}:".format(client.port)
        print stdout

    for client in slow_clients:
        stdout = client.get_stdout()
        print "---------------------------------------"
        print "Client blasted port {}:".format(client.port)
        print stdout if stdout else "CLIENT STUCK! moving on"
