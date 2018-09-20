import subprocess
import argparse


class memcached(object):
    """
    Stores memcached process state.

    Exposes a UDP and/or TCP port with the given port number(s).
    """

    def __init__(self, tcp_port, udp_port, nb_threads, debug):
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.nb_threads = nb_threads
        self.debug = debug

        self.args = ["memcached"]
        if debug:
            self.args.append("-vv")
        self.args.extend(["-p", str(tcp_port), "-u", str(udp_port), "-t", str(nb_threads)])
        self.p = subprocess.Popen(self.args)

    def stop(self):
        self.p.terminate()


def start_servers(tcp_port, udp_port, nb_threads, nb_servers, debug):
    mc_list = []
    for _ in range(nb_servers):
        mc_list.append(memcached(tcp_port, udp_port, nb_threads, debug))
        if udp_port > 0:
            udp_port += 1
        if tcp_port > 0:
            tcp_port += 1
    return mc_list


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", help="tcp port number", type=int)
    parser.add_argument("-u", help="udp port number", type=int)
    parser.add_argument("-t", help="Number of threads per server", type=int)
    parser.add_argument("--nb_servers", help="number of instances to create", type=int)
    parser.add_argument("--debug", help="Enable debugging", action="store_true")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    tcp_port = args.p if args.p else 12345
    udp_port = args.u if args.u else 12345
    nb_threads = args.t if args.t else 4
    nb_servers = args.nb_servers if args.nb_servers else 1
    debug = args.debug

    mc_list = start_servers(tcp_port, udp_port, nb_threads, nb_servers, debug)
    while True:
        quit = raw_input("quit? y/n")
        if "y" in quit:
            break

    for mc in mc_list:
        mc.stop()
