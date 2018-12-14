# NodeStat
Script for parsing and displaying node status information of the HPC Sapelo2 at UGA.

## Usage
* To check the status of all nodes in a queue
```
python3 node_stat.py -q batch
```

* To check the status of all nodes in a queue and display all the jobs running on that node
```
python3 node_stat.py -q batch --jobs
```

* To only display nodes that have available recourses (mem or cpus)
```
python3 node_stat.py -q highmem_q --avail
```

* To display the node with the most available memory and the most available cpu threads
```
python3 node_stat.py -q highmem_q --free
```

* To only display nodes with given memory and cpu availability
```
# displays HIGHMEM nodes with at least 40gb memory and 20 cpu threads available
python3 node_stat.py -q highmem_q -m 40 -t 20
```

## Common queues
* highmem = `highmem_q`
* batch = `batch`
* interative = `s_interq`
* GPU = `gpu_q`
