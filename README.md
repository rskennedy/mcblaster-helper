# mcblaster helper #

mcblaster is an old facebook performance tester for memcached. It supports udp and is small enough to modify for researchers. This repo contains helper scripts to run many instances of the client and the memcached servers.

### Setup ### 
1. Get mcblaster in one of the following two ways
    - from submodule, modified mcblaster that supports UDP SETs: `git submodule update --init`
    - from original source: https://github.com/fbmarc/facebook-memcached-old).
2. compile mcblaster (in `/tests`)
	- may have to disable Werror
	- Set environment variable `MCBLASTER_PATH` to the mcblaster executable
3. install memcached on receiving node (could be same as mcblaster node for local testing)
    - note that the script assumes you use a package manager for memcached. If you install from source it will take some hacking on `memcached.args` in `start-server.py` to get the servers up.

### Running ###
- Note that before running a GET only test, the servers must be populated. If you are using the submodule which is the default assumption, you should be able to do so with only UDP. However, the original mcblaster requires a TCP socket for SETs, so make sure to consider this before testing.

- __start servers__ creates a number of memcached servers. It will spawn _n_ instances from _port_ ... _port + n_. Be careful picking your range because this script does not handle collisions intelligently. Below are the configuration flags and their default values.
    - `-p` -- tcp port number [12345]
    - `-u` -- udp port number [12345]
    - `-t` -- number of threads per server [4]
    - `--nb_servers` -- number of instances to create [1]
    - `--debug` -- Enables debugging, specifically level 2 verbosity. [NO DEFAULT: lack of flag means false]
    
- __start clients__ runs n memcached performance testers... and accepts a lot of arguments. 
    - `--server`: hostname or ip of target machine ["localhost"]
    - `-p`: TCP port to begin scanning [0: UDP by default]
    - `-u`: UDP port to begin scanning [12345]
    - `-f`: source port aka flow. Only used by modified mcblaster. [None]
        - This value increments alongside the port number and should have space for its own non-overlapping range. For example if you wanted 10 clients and your udp port is 5000, your source port should be >= 5010 or <= 4990. 
    - `-k`: key size [1]
    - `-r`: GET requests per second [0]
    - `-t`: number of threads to use [None: mcblaster will decide how many to use]
    - `-w`: SET requests per second [0]
    - `-z`: value size [100]
    - `-g`: generation value [0]
    - `--nb_clients`: number of clients to create [1]
    - `--duration`: duration of client in seconds [5]

### Examples ###
#### Client ####
All defaults, TCP connection for SET and UDP for GET, one write per second:

`python start-clients.py -p 12345 -w 1`

Default server and port (localhost, udp starting at 12345), 5 SETs per second, 1000 clients

`python start-clients.py -f 12345 -w 5 --nb_clients 1000`

TCP only client, 20,000 GETs per second, 20 second duration, 4 threads:

`python start-clients.py --server <server> -p <portnum> -u 0 -r 20000 -t 4 --duration 20`  

100,000 SETs per second, 10 threads per client, 10 clients, 1024 value size:

`python start-clients.py -f 12335 -w 100000 -t 10 -z 1024 --nb_clients 10`  

 #### Server ####
 
 All defaults (TCP and UDP starting on 12345):
 
 `python start-servers.py`
 
 Default port (UDP only) with debugging enabled:
 
 `python start-servers.py -p 0 -u 12345 --debug`
 
 1000 servers, 1 thread each:
 
 `python start-servers.py --nb_servers 1000 -t 1`
 
 
### Current Limitations ###
- Currently dumps stdout from each mcblaster client onto console. Future improvement could be to parse this text and store the latency distribution and throughput in a dict so we can aggregate statistics over all the clients.
- setting value size seems to be broken for modified mcblaster. A value size of 100 results in this:
    - `Internal error: bufsize (120) is too small in compose_set(). Need 133 bytes`
