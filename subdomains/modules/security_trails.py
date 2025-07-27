#!/usr/bin/env python
import requests
import json
from sys import argv
from os import environ

API_KEY = environ.get("sectrails_key",None)

def check_key():
    if not API_KEY:
        raise ("No valid API key")    

def write_results(records):
    with open("subdomains.security_trails","a") as out:
        for record in records:
            hostname = record["domain"]["hostname"]
            if hostname:
                out.writelines(hostname)


def first_request(domain):
    query = f"SELECT domain.hostname FROM hosts WHERE domain.hostname LIKE '%.{domain}'"
    check_key()
    '-v' in argv and print("[+] Sending First Request")
    url = "https://api.securitytrails.com/v1/query/scroll/"
    headers = {
            "APIKEY": API_KEY,
            "Content-Type": "application/json"
    }
    data = {
            "query": query
    }
    response = requests.post(url, json=data, headers=headers)
    try:
        total_results = json.loads(response.text)["total"]["value"]
    except:
        raise "Invalid response"
    '-v' in argv and print(f"Total Results: {total_results}")
    write_results(json.loads(response.text)["records"])
    return json.loads(response.text)["id"]


def security_trails(domain,*args):
    check_key()
    scrol_id = first_request(domain=domain)
    num = 2
    while scrol_id:
        url= "https://api.securitytrails.com/v1/query/scroll/" + scrol_id
        '-v' in argv and print(f"Fetch Request Number: {num}, Send To: {url}")
        headers = {
            "APIKEY": API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        try:
           records = json.loads(response.text)["records"]
           write_results(records)
           scrol_id = json.loads(response.text)["id"]
           num+=1
        except:
            '-v' in argv and print("[-] Exit ...")
            '-v' in argv and print(response.status_code)
            '-v' in argv and print(response.text)
            exit()


if __name__ == "__main__":
    if len(argv) < 2:
        print(f"""USAGE:
            {argv[0]} <domain>""")
        exit()
    security_trails(argv[1])
