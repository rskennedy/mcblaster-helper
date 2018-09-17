import subprocess
import sys
import argparse

class memcached(object):
    """
    Stores memcached process state.

    Exposes a TCP (and optionally UDP) port with the given port number.
    """
    def __init__(self, port, debug, with_udp):
        self.port = port
        self.args = ["memcached", "-p", str(port)]
        if debug:
                self.args.append("-vv")
        if with_udp:
            self.args.extend(["-U", str(port)])
        self.p = subprocess.Popen(self.args)

    def stop(self):
        self.p.terminate()


def start_servers(starting_port, n, debug, with_udp):
    mc_list = []
    for i in range(n):
        port = starting_port + i
        mc_list.append(memcached(port, debug, with_udp))
    return mc_list

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "Not enough arguments. Usage: start-servers.py <start port> <number of instances> [--debug] [--udp]"
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("starting_port", help="Begin creating memcached servers on this port number", type=int)
    parser.add_argument("n", help="number of instances to create", type=int)
    parser.add_argument("--debug", help="Enable debugging", action="store_true")
    parser.add_argument("--udp", help="Enable udp port (uses same port number as tcp)", action="store_true")

    args = parser.parse_args()

    mc_list = start_servers(args.starting_port, args.n, args.debug, args.udp)
    while True:
        quit = raw_input("quit? y/n")
        if "y" in quit:
            break

    for mc in mc_list:
        mc.stop()
