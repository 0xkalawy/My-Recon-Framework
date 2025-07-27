#!/usr/bin/env python3

from sys import argv

ignore_ext = [".js",".png",".css",".jpg",".svg",".gif",".mov",".mp4",".woff",".woff2",".webp",".jpeg",".jfif",".webm",".ttf",".otf",".PNG",".JPG",".JPEG",".ico"]
def custom_wordlist(filepath:str):
    with open(filepath,'r') as file:
        for url in file.readlines():
            url = url.strip()
            if url.find("?")!=-1:
                url = url[:url.find("?")]
            uri = url.split("/")[3:]
            if any([url.endswith(ext) for ext in ignore_ext]):
                uri = uri[:-1]
            print('/'.join(uri))
            for i in uri:
                print(i)

if __name__ == "__main__":
    if len(argv) < 2:
        print(f"""Usage:
            {argv[0]} <urls-file>""")
        exit()
    custom_wordlist(argv[1])