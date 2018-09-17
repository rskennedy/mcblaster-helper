# mcblaster helper #

### Setup ### 
1. clone fbmarc/facebook-memcached-old
2. compile mcblaster (in `/tests`)
	- may have to disable Werror
	- Set environment variable `MCBLASTER_PATH` to the mcblaster executable
3. install memcached on receiving node (could be same as mcblaster node for local testing)
    - note that the script assumes you use a package manager for memcached. If you install from source it will take some hacking on `memcached.args` in `start-server.py` to get the servers up.

### Running ###
- Start servers takes a port number and number of instances. It will spawn _n_ instances from _port_ ... _port + n_. Be careful picking your range because this script does not handle collisions intelligently.
    - Optionally has debug flag (appends `-vv` to memcached) and udp flag (listens for tcp and udp on same port number).
    
- Start clients takes a lot of arguments. 
    - `server`: hostname or ip of target machine.
    - `starting_port`: first port number to attempt connection. Increment port number from here.
    - `rate`: Rate of get requests per second. mcblaster will attempt to be as precise as possible and report back exact number of requests.
        - defaults to `1000`
    - `n`: number of client instances to spawn. Note that these are all seperate mcblaster clients with their own output and performance statistics.
        - defaults to `1`
    - `duration`: How long each client should stay connected before closing.
        - defaults to `2`
    

### Current Limitations ###
- Only performs testing on `GET`. It would be no trouble to support `SET` so if that would be helpful let me know!
- Currently dumps stdout from each mcblaster client onto console. Future improvement could be to parse this text and store the latency distribution and throughput in a dict so we can aggregate statistics over all the clients.
