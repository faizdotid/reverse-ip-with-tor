###rekode? jan lupain author :)
import os
import requests
from threading import Thread
from queue import Queue
import re
import socket
from colorama import Fore, init
init(autoreset=True)


os.system('sudo killall tor')
rel_tor = 'service tor reload'
ipsl = []

def req():
    session = requests.Session()
    session.proxies.update({'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'})
    session.headers.update({'User-Agent': 'Mozilla'})
    session.timeout=14
    return session


request = req()


def reverse_ip(targ):
    api_url = 'https://api.hackertarget.com/reverseiplookup/?q='+targ
    try:
        req = request.get(api_url).text
        if 'No DNS' in req:
            print(Fore.RED+'FAILED! > '+targ)
        elif 'API count' in req:
            os.system(rel_tor)
            reverse_ip(targ)
        elif '429 Too Many' in req:
            os.system(rel_tor)
            reverse_ip(targ)
        else:
            domains = req.splitlines()
            print(Fore.GREEN+'HT | SUCCESS! > '+targ+' | '+str(len(domains)))
            for domain in domains:
                domain = domain.replace('webdisk.', '').replace('cpanel.', '').replace('autodiscover.', '').replace('cpcalendars.', '').replace('cpcontacts.', '').replace('webmail.', '').replace('mail.', '')
                save = open('rev.txt', 'a')
                save.write(domain+'\n')
                save.close()
    except Exception as ex:
        print(Fore.RED+str(ex))
        reverse_ip(targ)


def reverse_ip2(targ):
    api_url = 'https://viewdns.com/reverse-ip-lookup/'+targ
    try:
        req = request.get(api_url).text
        if 'We found' in req:
            domains = re.findall('<a href="https://viewdns.com/view-dns-records/(.*?)">', req)
            print(Fore.GREEN+'ViewDns | SUCCESS! > '+targ+' | '+str(len(domains)))
            for domain in domains:
                save = open('rev.txt', 'a')
                save.write(domain+'\n')
                save.close()
        elif 'Unable to do' in req:
            print(Fore.RED+'ViewDns | FAILED! > '+targ)
        else:
            os.system(rel_tor)
            reverse_ip2(targ)
    except Exception as ex:
        print(Fore.RED+str(ex))
        reverse_ip2(targ)


def rem_url(url):
    url = url.replace('http://', '').replace('https://', '').replace('/', '')
    try:
        ip = socket.gethostbyname(url)
        if ip not in ipsl:
            reverse_ip(ip)
            reverse_ip2(ip)
            ipsl.append(ip)
        else:
            print(Fore.RED+'DUPLICATE! > '+ip)
    except Exception as ex:
        print(Fore.RED+str(ex))


jobs = Queue()

def do(q):
    while not q.empty():
        targ = q.get()
        rem_url(targ)
        q.task_done()
    
    
def Main():
    print(Fore.GREEN+"""
───────╔════╦═══╦═══╗
───────║╔╗╔╗║╔═╗║╔═╗║
╔═╦══╦╗╠╣║║╚╣║─║║╚═╝║
║╔╣║═╣╚╝║║║─║║─║║╔╗╔╝
║║║║═╬╗╔╝║║─║╚═╝║║║╚╗
╚╝╚══╝╚╝─╚╝─╚═══╩╝╚═╝By FaizGans""")
    xxx = open(input('LIST ~# '), 'r').read().splitlines()
    os.system('service tor start')
    for x in xxx:
        jobs.put(x)
    th = input('THREADS ~# ')
    for i in range(int(th)):
        t = Thread(target=do, args=(jobs,))
        t.start()

Main()
