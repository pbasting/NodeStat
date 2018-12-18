# NodeStat
NodeStat is a script designed to retrieve node information from Sapelo2 and display it in a consise and easy to read format. The primary use for this script is to check the resource (CPU threads, memory) availability of nodes, so that users can determine the amount of resources to request for jobs. This should make it easier to tailor job submission scripts to avoid waiting in queues.



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
