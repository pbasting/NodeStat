#!/usr/bin/env python3

import subprocess
import time
import sys
import argparse

class Node:
    def __init__(self):
        self.total_cores = 0
        self.used_cores = 0
        self.total_mem = 0
        self.used_mem = 0
        self.id = ""
        self.jobs = []
        self.state = ""
        self.partitions = []
    
    def set_node_info(self, node_info, system):
        if system == "torque":
            for x in range(30,1, -1):
                node_info = node_info.replace(" "*x, " ")

            split_node_info = node_info.split(" ")
            self.id = split_node_info[0]
            self.state = split_node_info[1]

            cpu_info = split_node_info[2].split(":")
            self.total_cores = int(cpu_info[1])
            self.used_cores = self.total_cores - int(cpu_info[0])

            mem_info = split_node_info[3].split(":")
            self.total_mem = int(mem_info[1])//1000
            self.used_mem = (int(mem_info[1]) - (int(mem_info[0])))//1000
        
        else:
            split_node_info = node_info.split(" ")
            for info in split_node_info:
                split_info = info.split("=")
                if "NodeName" == split_info[0]:
                    self.id = split_info[1]
                if "State" == split_info[0]:
                    self.state = split_info[1]
                if "CPUAlloc" == split_info[0]:
                    self.used_cores = int(split_info[1])
                if "CPUTot" == split_info[0]:
                    self.total_cores = int(split_info[1])
                if "AllocMem" == split_info[0]:
                    self.used_mem = int(split_info[1])//1000
                if "FreeMem" == split_info[0]:
                    try:
                        self.total_mem = int(split_info[1])//1000
                    except:
                        self.total_mem = 0
                if "Partitions" == split_info[0]:
                    self.partitions = split_info[1].split(",")




def main():
    args = parse_args()
    line_count = 0
    while True:
        try:
            nodes = get_nodes(args.group, args.system)
            nodes = sort_nodes(nodes,"M")
            node_info = ["       "+("-"*10)+" CPU "+("-"*10)+"     "+("-"*10)+" MEM "+("-"*10)+"  "+(" "*39)+"\n"]
            if args.free:
                node_info = get_best_nodes(nodes, node_info)
            
            elif args.mem > 0 or args.threads > 0:
                node_info = get_nodes_with_avail(nodes, args.mem, args.threads, args.group, node_info)
            
            else:
                for node in nodes:
                    if args.avail != True:
                        node_info.append(format_node_info(node))
                    else:
                        offline_nodes = ["Down","Offline","Busy","DOWN","DOWN*"]
                        if node.state not in offline_nodes and (node.total_cores - node.used_cores) > 0 and (node.total_mem - node.used_mem) > 0:
                            node_info.append(format_node_info(node))

            job_info = []
            # gets job info and displays nodes and jobs
            if args.job == True:
                job_info = get_job_info(args.group, args.system)
                job_info = format_job_info(job_info, args.system)
                if(line_count > 0):
                    for i in range(0,line_count):
                        subprocess.call(["tput","cuu1"])
                        subprocess.call(["tput","el"])

                display_node_info(node_info)
                # print("\n") # extra gap between nodes and jobs?
                display_job_info(job_info)

            # just displays nodes
            else:
                if(line_count > 0):
                    for i in range(0,line_count):
                        subprocess.call(["tput","cuu1"])
                        subprocess.call(["tput","el"])
                display_node_info(node_info)


            if args.loop_mode != None:
                time.sleep(int(args.loop_mode))
                line_count = len(node_info)
                if args.job == True:
                    line_count += (len(job_info) + 3)
                    
            else:
                sys.exit(0)

        except KeyboardInterrupt:
            sys.stderr.write("\n")
            sys.exit()


def parse_args():
    parser = argparse.ArgumentParser(description='Script to check status of nodes on Sapelo2')
    optional = parser._action_groups.pop()
    required = parser.add_argument_group("required arguments")

    required.add_argument('-q',action="store",dest="group", help="group of nodes to display ex. highmem_q")
    optional.add_argument('-l',action="store", dest="loop_mode",help="runs program in loop, sets number of seconds to wait to refresh")
    optional.add_argument('--jobs',action="store_true", dest="job",help="outputs job information running in group")
    optional.add_argument('--avail',action="store_true", dest="avail",help="only outputs nodes with available resources")
    optional.add_argument('--free',action="store_true", dest="free",help="only outputs nodes with the most available memory and cpu threads")
    optional.add_argument('-m',action="store", dest="mem",help="only outputs nodes with the given available memory or more (gb)")
    optional.add_argument('-t',action="store", dest="threads",help="only outputs nodes with the given available threads or more")
    optional.add_argument("-s",action="store", dest="system", help="specify which queueing system to use: torque or slurm [torque]")


    parser._action_groups.append(optional)
    args = parser.parse_args()

    if args.group is None:
        sys.stderr.write("-q option missing\n")
        sys.stderr.write("\nusage: python3 node_stat.py -q highmem_q --jobs --avail\n")
        sys.exit(1)

    if args.mem is None:
        args.mem = 0
    else:
        args.mem = int(args.mem)
    
    if args.threads is None:
        args.threads = 0
    else:
        args.threads = int(args.threads)
    
    valid_systems = ["torque", "slurm"]
    if args.system is None:
        args.system = "torque"
    else:
        args.system = args.system.lower()
        if args.system not in valid_systems:
            print(args.system, "is not a valid queueing system... valid systems:", " ".join(valid_systems), file=sys.stderr)
            sys.exit(1)

    return args


def get_nodes(group, system):
    nodes = []

    if system == "torque":
        pbsnodes_text = subprocess.Popen(["mdiag","-n","-v"], stdout= subprocess.PIPE)
        for line in pbsnodes_text.stdout:
            line = line.decode()
            if line.find("["+group+"]") != -1 and line.find("["+group+"][") == -1:
                node = Node()
                node.set_node_info(line, system)
                nodes.append(node)
    
    else:
        node_info = ""
        pbsnodes_text = subprocess.Popen(["scontrol","show","nodes"], stdout=subprocess.PIPE)
        for line in pbsnodes_text.stdout:
            line = line.decode()
            if "NodeName=" in line:
                if node_info != "":
                    node = Node()
                    node.set_node_info(node_info, system)
                    if group in node.partitions:
                        nodes.append(node)
                    node_info = ""

            node_info += line.replace("\n", " ")
        
        if node_info != "":
            node = Node()
            node.set_node_info(node_info, system)
            if group in node.partitions:
                nodes.append(node)
        
    if len(nodes) == 0:
        sys.stderr.write("No nodes found in group: "+group+"\nExiting...\n")
        sys.exit(1)

    return nodes

def sort_nodes(nodes, mode):
    if mode == "M":
        nodes = sort_nodes_mem(nodes)

    elif mode == 'C':
        nodes = sort_nodes_cpu(nodes)

    nodes = sort_nodes_state(nodes)

    return nodes

def sort_nodes_state(nodes):
    states = ["Busy","Drained","Down","DOWN","DOWN*"]
    for state in states:
        swapped = True
        while (swapped == True):
            swapped = False
            for x in range(0,len(nodes)-1):
                if ((nodes[x].state == state) and (nodes[x+1].state != state)):
                    swapped = True
                    tmp = nodes[x]
                    nodes[x] = nodes[x+1]
                    nodes[x+1] = tmp

    return nodes

def sort_nodes_mem(nodes):
    swapped = True
    while(swapped == True):
        swapped = False
        for x in range(0,len(nodes)-1):
            if (nodes[x].total_mem - nodes[x].used_mem) < (nodes[x+1].total_mem - nodes[x+1].used_mem):
                swapped = True
                tmp = nodes[x]
                nodes[x] = nodes[x+1]
                nodes[x+1] = tmp
    
    return nodes

def sort_nodes_cpu(nodes):
    swapped = True
    while(swapped == True):
        swapped = False
        for x in range(0,len(nodes)-1):
            if (nodes[x].total_cores - nodes[x].used_cores) < (nodes[x+1].total_cores - nodes[x+1].used_cores):
                swapped = True
                tmp = nodes[x]
                nodes[x] = nodes[x+1]
                nodes[x+1] = tmp
    
    return nodes


def get_best_nodes(nodes, node_info):
    # gets node with max mem avail and max threads avail
    best_cpu_node = get_best_node(nodes,"C")
    best_mem_node = get_best_node(nodes,"M")

    if best_cpu_node != best_mem_node:
            node_info.append(format_node_info(best_mem_node))
            node_info.append(format_node_info(best_cpu_node))
    else:
        node_info.append(format_node_info(best_cpu_node))
    node_info.append("\n")
    node_info.append("Max mem job available: "+str(best_mem_node.total_cores - best_mem_node.used_cores)+" threads, "+str(best_mem_node.total_mem - best_mem_node.used_mem)+" gb mem\n")
    node_info.append("Max cpu job available: "+str(best_cpu_node.total_cores - best_cpu_node.used_cores)+" threads, "+str(best_cpu_node.total_mem - best_cpu_node.used_mem)+" gb mem\n")

    return node_info


def get_best_node(nodes, mode):
    if mode == "C": 
        nodes = sort_nodes_mem(nodes)
        nodes = sort_nodes_cpu(nodes)

    else:
        nodes = sort_nodes_cpu(nodes)
        nodes = sort_nodes_mem(nodes)

    nodes = sort_nodes_state(nodes)

    swapped = True
    while (swapped == True):
        swapped = False
        for x in range(0,len(nodes)-1):
            if ((nodes[x].used_cores == nodes[x].total_cores) and (nodes[x+1].used_cores != nodes[x+1].total_cores)):
                swapped = True
                tmp = nodes[x]
                nodes[x] = nodes[x+1]
                nodes[x+1] = tmp

    return nodes[0]

def format_node_info(node):
    gray = "\033[0;37m"
    red = "\033[0;31m"
    green = "\033[0;32m"
    orange = "\033[0;33m"
    blue = "\033[0;34m"
    no_color = "\033[0m"

    if node.total_cores > 0:
        percent_used = (node.used_cores / node.total_cores) * 100
        percent_used = int(percent_used/4)

        used_cores = "|"*percent_used
        avail_cores = "|"*(25 - percent_used)
    else:
        used_cores = ""
        avail_cores = " "*25

    if node.total_mem > 0:
        if node.used_mem > node.total_mem:
            node.used_mem = node.total_mem
        percent_used = (node.used_mem / node.total_mem) * 100
        percent_used = int(percent_used/4)
        used_mem = "|"*percent_used
        avail_mem = "|"*(25 - percent_used)
    else:
        used_mem = ""
        avail_mem = " "*25

    id_gap = ""
    if len(node.id) == 2:
        id_gap = "    "
    elif len(node.id) == 3:
        id_gap = "   "
    elif len(node.id) == 4:
        id_gap = "  "
    elif len(node.id) == 5:
        id_gap = " "

    pre_cpu_gap = " "
    if node.used_cores < 10 and node.total_cores < 10:
        cpu_gap = "  "
    elif node.used_cores < 10:
        cpu_gap = " "
    else:
        cpu_gap = ""

    if node.used_mem < 10:
        mem_gap = " "*3
    elif node.used_mem < 100:
        mem_gap = " "*2
    elif node.used_mem < 1000:
        mem_gap = " "
    else:
        mem_gap = ""
    
    if node.total_mem >= 1000:
        post_mem_gap = " "
    elif node.total_mem >= 100:
        post_mem_gap = "  "
    elif node.total_mem >= 10:
        post_mem_gap = "   "
    else:
        post_mem_gap = "    "

    # prints grey for down or drained nodes
    offline_nodes = ["Down","Offline","Busy","Drained","DOWN","DOWN*"]
    if node.state not in offline_nodes:
        display = node.id+id_gap+"[ "+red+used_cores+green+avail_cores+no_color+" ] [ "+red+used_mem+blue+avail_mem+no_color+" ]"+pre_cpu_gap+"CPU: "+cpu_gap+ \
                    red+str(node.used_cores)+no_color+"/"+green+str(node.total_cores)+no_color+ \
                    "  MEM:"+mem_gap+red+str(node.used_mem)+no_color+"/"+blue+str(node.total_mem)+no_color+post_mem_gap+"GB\t"+node.state+"\n"
    else:
         display = gray+node.id+id_gap+"[ "+used_cores+avail_cores+" ] [ "+used_mem+avail_mem+" ]"+pre_cpu_gap+"CPU: "+cpu_gap+ \
                    str(node.used_cores)+"/"+str(node.total_cores)+ \
                    "  MEM:"+mem_gap+str(node.used_mem)+"/"+str(node.total_mem)+post_mem_gap+"GB\t"+node.state+no_color+"\n"

    return(display)


def get_nodes_with_avail(nodes, mem, threads, group, node_info):
    for node in nodes:
        if ((node.total_mem - node.used_mem) >= mem) and ((node.total_cores - node.used_cores) >= threads) and (node.state == "Running" or node.state == "Idle"):
            node_info.append(format_node_info(node))
                
        if len(node_info) <= 1:
            sys.stderr.write("No nodes in "+group+" with at least "+str(mem)+"gb memory and "+str(threads)+" threads available\n")
            # node_info = ["No nodes in "+args.group+" with at least "+str(args.mem)+"gb memory and "+str(args.threads)+" threads available\n"]
            node_info = []

    return node_info


def get_job_info(group, system):
    job_info = []
    if system == "torque":
        qstat_text = subprocess.Popen(["qstat","-f",group], stdout= subprocess.PIPE)
        info = ""
        for line in qstat_text.stdout:
            line = line.decode()
            if line.find("Job Id:") != -1:
                if info != "":
                    job_info.append(info)
                    info = line
                else:
                    info = line
            else:
                info += (line)
        
        job_info.append(info)
    
    else:
        qstat_text = subprocess.Popen(["sacct","--format","partition,NodeList,JobID,User,jobname,State,ReqNodes,ReqCPUs,ReqMem,Timelimit,Elapsed,CPUTime","-p"], stdout=subprocess.PIPE)
        info = ""
        for ln,line in enumerate(qstat_text.stdout):
            if ln > 0:
                line = line.decode()
                split_line = line.split("|")
                if ".extern" not in split_line[2] and group in split_line[0]:
                    job_info.append(split_line)
            
    return job_info


def format_job_info(job_info, system):
    jobs = []
    for job in job_info:           
        req_mem = "1gb"
        wall_time = "00:00:00"
        cpu_time = "00:00:00"
        state = "C"
        node_id = "?"
        if system == "torque":
            job = job.split("\n")
            for line in job:
                if line.find("Job Id:") != -1:
                    job_id = line[line.find(":")+2:]
                    job_id = job_id.replace("\n","")
                if line.find("Job_Name =") != -1:
                    name = line[line.find("=")+2:]
                    name = name.replace("\n","")

                elif line.find("Job_Owner =") != -1:
                    line = line[line.find("=")+2:]
                    owner = line[:line.find("@")]

                elif line.find("resources_used.cput =") != -1:
                    cpu_time = line[line.find("=")+2:]
                    cpu_time = cpu_time.replace("\n","")

                elif line.find("resources_used.walltime =") != -1:
                    wall_time = line[line.find("=")+2:]
                    wall_time = wall_time.replace("\n","")
                
                elif line.find("Resource_List.walltime =") != -1:
                    req_time = line[line.find("=")+2:]
                    req_time = req_time.replace("\n","")

                elif line.find("job_state =") != -1:
                    state = line[line.find("=")+2:]
                    state = state.replace("\n","")

                elif line.find("Resource_List.mem =") != -1:
                    req_mem = line[line.find("=")+2:]
                    req_mem = req_mem.replace("\n","")

                elif line.find("Resource_List.nodes =") != -1:
                    line = line[line.find("=")+2:]
                    nodes = line[:line.find(":")]
                    req_cpu = line[line.find("=")+1:]
                    req_cpu = req_cpu.replace("\n","")
                    if req_cpu.find(":") != -1:
                        req_cpu = req_cpu[:req_cpu.find(":")]

                elif line.find("exec_host =") != -1:
                    line = line[line.find("=")+2:]
                    node_id = line[:line.find("/")]
            
        else:
            line = job
            node_id = line[1]
            job_id = line[2]
            owner = line[3]
            name = line[4]
            state = line[5][0]
            nodes = line[6]
            req_cpu = line[7]
            req_mem = line[8].replace("Mn","")
            req_mem = str(int(req_mem)//1000)
            req_time = line[9]
            wall_time = line[10]
            cpu_time = line[11]

        if state == 'R':
            out_vals = [node_id,job_id,owner,name,state, nodes, req_cpu,req_mem,req_time,wall_time, cpu_time]
            jobs.append(out_vals)

    return(jobs)

def display_node_info(node_info):
    # bkg_white = '\e[107m'
    # bkg_none = '\e[49m'
    # txt_black = '\e[30m'
    # txt_none = '\e[39m'

    for x,node in enumerate(node_info):
        # if x == 0:
        #     subprocess.call(["printf",bkg_white])
        #     subprocess.call(["printf",txt_black])
        # elif x == 1:
        #     subprocess.call(["printf",bkg_none])
        #     subprocess.call(["printf",txt_none])

        subprocess.call(["printf",node])

def display_job_info(out_vals):
    bkg_white = '\e[107m'
    bkg_none = '\e[49m'
    txt_black = '\e[30m'
    txt_none = '\e[39m'

    labels = ["Node","Job ID","User","Name","S","NDS","THR","MEM","Max Time","Time","CPU Time"]
    widths = [4,14,8,16,1,3,3,5,9,9,9]
    gap = " "*2 # space between columns


    print("_"*102)
    for x in range(0,len(labels)):
        print(labels[x]+(" "*(widths[x]-len(labels[x]))), end=gap)
    
    print("")
    print("-"*102)

    for x in range(0,len(out_vals)):
        for y in range(0,len(out_vals[x])):        
            if len(out_vals[x][y]) > widths[y]:
                print(out_vals[x][y][:widths[y]],end=gap)
            else:
                print(out_vals[x][y]+(" "*(widths[y]-len(out_vals[x][y]))),end=gap)

        print("")

if __name__ == "__main__":
    main()