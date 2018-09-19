import subprocess
import time
import argparse
import os

# path to mcblaster EXECUTABLE
MCBLASTER_PATH = os.environ['MCBLASTER_PATH']
# indexes into mcblaster argument string
port_index = 2
flow_index = 4


class client(object):
    def __init__(self, mcblaster_args):
        self.args = mcblaster_args
        self.port = mcblaster_args[port_index]
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
        If the process is not finished, we let the caller know
        to move on, and it should recheck this client at a later time.
        :return: tuple with stdout and stderr
        """
        if self.process.poll() is None:
            return None
        return self.process.communicate()


def form_mcblaster_args(
        server="localhost",
        tcp_port=0,
        udp_port=12345,
        flow=None,
        key_size=1,
        read_rate=None,
        nb_threads=None,
        write_rate=None,
        value_size=50,
        duration=5,
):
    args = [MCBLASTER_PATH]
    if tcp_port > 0:
        args.extend(["-p", str(tcp_port)])
    else:
        args.extend(["-u", str(udp_port)])
    if flow is not None:
        args.extend(["-f", str(flow)])
    if read_rate is not None:
        args.extend(["-r", str(read_rate)])
    if nb_threads is not None:
        args.extend(["-t", str(nb_threads)])
    if write_rate is not None:
        args.extend(["-w", str(write_rate)])
    args.extend(["-k", str(key_size), "-z", str(value_size)])
    args.extend(["-d", str(duration)])
    args.append(server)

    return args


def increment_port_mcblaster_args(mcblaster_args):
    """
    Increment the port value of the mcblaster arguments list.
    Note that if the arguments list structure is changed, the
    port index should be changed as well.
    :param mcblaster_args: List of strings that will eventually
     be called with mcblaster.
    :return:
    """
    mcblaster_args[port_index] = str(int(mcblaster_args[port_index]) + 1)


def increment_flow_mcblaster_args(mcblaster_args):
    """
    Increment the flow value of the mcblaster arguments list.
    Note that if the arguments list structure is changed, the
    flow index should be changed as well.
    :param mcblaster_args: List of strings that will eventually
     be called with mcblaster.
    :return:
    """
    mcblaster_args[flow_index] = str(int(mcblaster_args[flow_index]) + 1)


def start_clients(mcblaster_args, generation=0, nb_clients=1):
    """
    Creates n client objects that will blast memcached servers.
    :param mcblaster_args: List of strings that will eventually
     be called with mcblaster.
    :param generation: TODO
    :param nb_clients: number of clients to create.
    :return: list of client objects all of which have been started.
    """
    client_list = []
    """
    Create each client object which will create a mcblaster subproc on init.
    """
    for i in range(nb_clients):
        client_list.append(client(mcblaster_args))
        increment_port_mcblaster_args(mcblaster_args)
        increment_flow_mcblaster_args(mcblaster_args)
    return client_list


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", help="server hostname or ip", type=str)
    parser.add_argument("-p", help="TCP port to begin scanning", type=int)
    parser.add_argument("-u", help="UDP port to begin scanning", type=int)
    parser.add_argument("-f", help="flow", type=int)
    parser.add_argument("-k", help="key size", type=int)
    parser.add_argument("-r", help="GET requests per second", type=int)
    parser.add_argument("-t", help="number of threads to use", type=int)
    parser.add_argument("-w", help="SET requests per second", type=int)
    parser.add_argument("-z", help="value size", type=int)
    parser.add_argument("-g", help="generation value", type=int)
    parser.add_argument("--nb_clients", help="number of clients to create", type=int)
    parser.add_argument("--duration", help="duration of client in seconds", type=int)
    return parser.parse_args()


if __name__ == '__main__':

    args = parse_args()

    server = args.server if args.server else "localhost"
    tcp_port = args.p if args.p else 0
    udp_port = args.u if args.u else 12345
    flow = args.f if args.f else None
    key_size = args.k if args.k else 1
    read_rate = args.r if args.r else None
    nb_threads = args.t if args.t else None
    write_rate = args.w if args.w else None
    value_size = args.z if args.z else 50
    duration = args.duration if args.duration else 5
    generation = args.g if args.g else 0
    nb_clients = args.nb_clients if args.nb_clients else 1

    if read_rate == 0 and write_rate == 0:
        print "Must specify set rate (-w) or get rate (-r) or both."
        exit(1)

    mcblaster_args = form_mcblaster_args(
        server,
        tcp_port,
        udp_port,
        flow,
        key_size,
        read_rate,
        nb_threads,
        write_rate,
        value_size,
        duration,
    )

    clients = start_clients(mcblaster_args, generation, nb_clients)

    # give the clients a chance to talk to their servers
    time.sleep(duration + 1)
    slow_clients = []

    for client in clients:
        stdout = client.get_stdout()
        if stdout is None:
            slow_clients.append(client)
            continue

        print "---------------------------------------"
        print "Client blasted port {}. stdout below:".format(client.port)
        print stdout

    for client in slow_clients:
        stdout = client.get_stdout()
        print "---------------------------------------"
        print "Client blasted port {}. stdout below:".format(client.port)
        print stdout if stdout else "CLIENT STUCK! moving on"