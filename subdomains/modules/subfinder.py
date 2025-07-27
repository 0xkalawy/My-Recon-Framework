import subprocess
from sys import argv
def subfinder(domain):
    try:
        output = subprocess.check_output(
            ["subfinder", "-stats", "-all", "-d", domain],
            stderr=subprocess.DEVNULL,
        )
        with open("subdomains.subfinder", "w") as out:
            out.write(output.decode())
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error running subfinder: {e}")
    
    
if __name__ =="__main__":
    if len(argv) < 2:
        print(f"""Usage:
              {argv[0]} <domain>""")
        exit()
    subfinder(argv[1])