'''

Pass data via authentication of an FTP session in the username field

'''

import os
import socket
import sys
import shutil
import base64
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

exfil_directory = os.path.join(os.getcwd(), "data") 




class MyHandler(FTPHandler):
    def on_connect(self):
        print "%s:%s connected" % (self.remote_ip, self.remote_port)

    def on_disconnect(self):
        # do something when client disconnects
	print "USER %s" % (self.username)
	info = ""  
        try:
	  if ";" not in self.username:
		tmp1 = exfil_directory + "/tmpfileX"
	  	info = base64.b64decode(str(self.username).strip())
		with open(tmp1, 'ab') as f:
		  f.write(info)
	  else:
		#copy tmp file to file name
		filename = self.username.split(';')[1].strip()
		filename = exfil_directory + "/"+filename
		print filename
		shutil.copyfile("/opt/Egress-Assess/data/tmpfileX", filename)
		os.remove("/opt/Egress-Assess/data/tmpfileX")
	except Exception as e:
	  print "Error: %s" % (e)
	  pass
        #there looks to be a on_login_failed(self , username, password)
        pass

    def on_login(self, username):
        # do something when user login
        print "%s logging in" % (username) #this may not work because we never fully login
        pass

    def on_logout(self, username):
        # do something when user logs out
        pass

    def on_file_sent(self, file):
        # do something when a file has been sent
        pass

    def on_file_received(self, file):
        # do something when a file has been received
        pass

    def on_incomplete_file_sent(self, file):
        # do something when a file is partially sent
        pass

    def on_incomplete_file_received(self, file):
        # remove partially uploaded files
        import os
        os.remove(file)


class Server:

    def __init__(self, cli_object):
        self.protocol = "ftp_auth"
        self.username = cli_object.username
        self.password = cli_object.password
        self.data_directory = ""
        if cli_object.server_port:
            self.port = int(cli_object.server_port)
        else:
            self.port = 21
	if cli_object.ip:
	    self.ip = cli_object.ip
	else:
	    self.ip = None

    def serve(self):
        # current directory
        exfil_directory = os.path.join(os.getcwd(), "data")
        loot_path = exfil_directory + "/"

        # Check to make sure the agent directory exists, and a loot
        # directory for the agent.  If not, make them
        if not os.path.isdir(loot_path):
            os.makedirs(loot_path)

        try:
            authorizer = DummyAuthorizer()
            authorizer.add_user(
                self.username, self.password,
                loot_path, perm="elradfmwM")

            handler = MyHandler
            handler.authorizer = authorizer

            # Define a customized banner (string returned when client connects)
            handler.banner = "Connecting to Egress-Assess's FTP server!"
            #Define public address and  passive ports making NAT configurations more predictable
            handler.masquerade_address = self.ip
            handler.passive_ports = range(60000, 60100)
            #handler.log_prefix = '%(username)s'
            
	    try:
                server = FTPServer(('', self.port), handler)
                server.serve_forever()
            except socket.error:
                print "[*][*] Error: Port %d is currently in use!" % self.port
                print "[*][*] Error: Please restart when port is free!\n"
                sys.exit()
        except ValueError:
            print "[*] Error: The directory you provided may not exist!"
            print "[*] Error: Please re-run with a valid FTP directory."
            sys.exit()
        return
