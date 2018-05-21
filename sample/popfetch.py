
import re, string, os,sys
from subprocess import Popen,PIPE
import logging





local_user       = sys.argv[1]
remote_user      = sys.argv[2]
mail_server      = "146.141.27.10"
ps_output_arg    = "-o command"
ps_user_flag     = "-U"   # change to "-u" on Linux
remote_pop_port  = "993"
local_pop_port   = "10993"
remote_smtp_port = "25"
local_smtp_port   = "10025"
ssh_args         = " -f -L "
delay            = " 1119 "
id_arg           =  "/Users/"+remote_user+"/.ssh/id_dsa"



#---------------------------------

poparg = local_pop_port+":"+mail_server+":"+remote_pop_port
remoteid = remote_user+"@"+mail_server

log_file  = "%s/.pop.log"%local_user
lock_file = "%s/.pop.lock"%local_user
pid_file = "%s/.pid.lock"%local_user

if os.access(lock_file,os.R_OK): sys.exit(0)
lf  = open(lock_file,"w")
lf.write(lock_file)
lf.close()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename=log_file,
                    filemode='a')


#------------------------------------------------


def get_pid():
    cmd = Popen(["ps",ps_user_flag,local_user],stdout=PIPE)
    lines = cmd.stdout.readlines()
    for line in lines:
	if poparg in line:
	    match = re.search("(\d+)\W(.*)",line)
	    pid =  match.group(1)
	    return pid
    return -1

def get_old_pid():
    if os.access(pid_file,os.R_OK):
        pfile = open(pid_file)
        line = pfile.readline()
        oldpid = line.rstrip()
        return oldpid
    return -2

def check_open_tunnel():
    pid = get_pid()
    oldpid = get_old_pid()
    wfile = open(pid_file,"w")
    wfile.write(str(pid))
    wfile.close()
    if pid == oldpid:
       os.system("kill -9 "+pid)
       logging.debug("Killing "+pid)
       pid = -1
    return pid
    

def valid_connection():
    cmd = Popen(["ssh","-i",id_arg,remoteid,"whoami"],stdout=PIPE,stderr=PIPE)
    lines = cmd.stderr.readlines()
    for line in lines:
	if "nreachable" in line:
            logging.info("No valid connection: "+line)
	    return False
	elif "No address" in line:
            logging.info("No valid connection: "+line)            
	    return False
    logging.debug("Valid connection found")
    return True

def get_mail():
    if not valid_connection(): return None
    pid = check_open_tunnel()
    if pid<0:
        cmd = Popen(["ssh","-i",id_arg,"-f","-L",poparg,remoteid,"sleep",delay],stdout=PIPE)
        os.system("sleep 3")


logging.info("Doing popfetch")
get_mail()
os.system("/bin/rm "+lock_file)


