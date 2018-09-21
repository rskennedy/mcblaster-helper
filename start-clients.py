import subprocess
import time
import argparse
import os

# path to mcblaster EXECUTABLE
MCBLASTER_PATH = os.environ['MCBLASTER_PATH']
# indexes into mcblaster argument string
port_index = 2
flow_index = 4


class EmptyStdoutError(Exception):
    pass


class stats(object):
    def __init__(self, request_type=None, throughput=None, avg=None, ld={}):
        self.request_type = request_type
        self.throughput = throughput
        self.avg = avg
        self.lat_distribution = ld

    def pretty_print(self):
        print "request type: {}".format(self.request_type)
        print "throughput: {} requests per second".format(self.throughput)
        print "average: {} ms".format(self.avg)
        print "latency distribution: {}".format(self.lat_distribution)


class client(object):
    def __init__(self, mcblaster_args, log_path_suffix=None):
        self.args = mcblaster_args
        self.port = mcblaster_args[port_index]
        self.log_file_path, log_file = self.create_log(log_path_suffix)
        self.read_stats = None
        self.write_stats = None
        self.process = subprocess.Popen(self.args, stdout=log_file)
        log_file.close()

    def stop(self):
        while self.process.poll() is None:
            time.sleep(1)
        self.log_file_path.close()

    def create_log(self, log_path_suffix=None):
        file_path = "logs/mcb_{}".format(self.port)
        if log_path_suffix is not None:
            file_path += log_path_suffix
        f = open(file_path, "w+")
        f.write("mcblaster arguments: {}\n\nSTDOUT:\n".format(str(self.args)))
        f.flush()
        return file_path, f

    def get_stats(self, request_type):
        if "get" == request_type:
            stats = self.read_stats
        elif "set" == request_type:
            stats = self.read_stats
        else:
            return None
        if stats is None:
            self.parse_stats()
        return stats

    def parse_stats(self):
        if self.process.poll() is None:
            return None

        curr_stats = None
        with open(self.log_file_path, "r") as f:
            for line in f:
                if line.startswith("Request type"):
                    request_type = line.split(None)[-1].strip()
                    if request_type == "get":
                        self.read_stats = stats(request_type)
                        curr_stats = self.read_stats
                    else:
                        self.write_stats = stats(request_type)
                        curr_stats = self.write_stats
                elif line.startswith("Rate per second"):
                    curr_stats.throughput = int(line.split(None)[-1].strip())
                elif line.startswith("RTT min"):
                    curr_stats.avg = int(line.split('/')[3].strip())

                elif line.startswith("RTT distribution for 'get'"):
                    curr_stats = self.read_stats
                elif line.startswith("RTT distribution for 'set'"):
                    curr_stats = self.write_stats

                elif line.startswith("["):
                    interval_start = int(line.split("-", 1)[0].strip()[1:])
                    height = int(line.split(None)[-1].strip())
                    curr_stats.lat_distribution[interval_start] = height

                elif line.startswith("Over 10000"):
                    curr_stats[10000] = line.split(None)[-1].strip()

        if curr_stats is None:
            raise EmptyStdoutError(
                "Log file '{}' has no output. Mcblaster most likely failed.".format(self.log_file_path))


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


def start_clients(mcblaster_args, generation=0, nb_clients=1, using_flow=False, with_single_server=False):
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
        if with_single_server is False:
            client_list.append(client(mcblaster_args))
            increment_port_mcblaster_args(mcblaster_args)
        else:
            client_list.append(client(mcblaster_args, log_path_suffix="_{}".format(i)))
        if using_flow:
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
    parser.add_argument("--single_server", help="n clients connect to 1 server", action="store_true")
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
    using_flow = flow is not None
    with_single_server = args.single_server

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

    clients = start_clients(mcblaster_args, generation, nb_clients, using_flow, with_single_server)

    # give the clients a chance to talk to their servers
    time.sleep(duration + 1)
    slow_clients = []
    total_stats = stats(request_type="get", throughput=0, avg=0)
    client_count = 0

    for client in clients:
        read_stats = client.get_stats("get")
        if read_stats is None:
            slow_clients.append(client)
            continue
        client_count += 1
        total_stats.throughput += read_stats.throughput
        total_stats.avg += read_stats.avg
        for (interval_start, height) in read_stats.lat_distribution:
            try:
                total_stats.lat_distribution[interval_start] += height
            except KeyError:
                total_stats.lat_distribution[interval_start] = height

    for client in slow_clients:
        client.process.wait()
        read_stats = client.get_stats("get")
        if read_stats is None:
            print "Client with dest port {} is STUCK! Moving on".format(client.port)
            continue
        client_count += 1
        total_stats.throughput += read_stats.throughput
        total_stats.avg += read_stats.avg
        for interval_start, height in read_stats.lat_distribution.iteritems():
            try:
                total_stats.lat_distribution[interval_start] += height
            except KeyError:
                total_stats.lat_distribution[interval_start] = height

    if client_count > 0:
        total_stats.avg /= client_count

    print "Aggregated statistics for {} clients: ".format(client_count)
    total_stats.pretty_print()
