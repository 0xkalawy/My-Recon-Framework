#!/usr/bin/env python3

from modules.netcraft import *
from modules.security_trails import *
from modules.subfinder import subfinder
from modules.recursive import *
from threading import Thread
from sys import argv
from subprocess import run

if __name__ == "__main__":
    if len(argv)<2:
        print(f"""Usage:
              {argv[0]} <domain>""")
        exit()
    
    t1 = Thread(target=netcraft,args=[argv[1],'-v' if '-v' in argv else ''])
    t2 = Thread(target=security_trails,args=[argv[1],'-v' if '-v' in argv else ''])
    t3 = Thread(target=subfinder,args=[argv[1]])


    t1.start()
    t2.start()
    t3.start()

    t1.join()
    t2.join()
    t3.join()

    run("cat subdomains.* > subdomains", shell=True)
    run("sort -u subdomains > x && mv x subdomains", shell=True)
    recursive("subdomains")
    run("ffuf -u https://FUZZ1.FUZZ2 -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt:FUZZ1 -w subdomains.alot:FUZZ2",shell=True)