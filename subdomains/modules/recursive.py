# This script does fuzzing on the domains that has more than 3 parts.

from sys import argv
import subprocess

def recursive(filename):
    with open(filename,"r") as file:
        for line in file.readlines():
            line = line.strip().split(".")
            if (len(line) == 4 and not line[0].startswith("www") and not line[0].startswith('ww')) or len(line)>4:
                with open("subdomains.alot","a") as file:
                    file.write(".".join(line[1:])+"\n")
     
if __name__ == "__main__":
    if len(argv) < 2:
        print(f"""Usage:
          {argv[0]} <domain-file>""")
        exit()
    recursive(argv[1])
    