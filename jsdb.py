#!env python
"""
JSDB CLI
--------

This command line tool is used to interact with any JSDB client that is 
connecting to this tool so that you can interact with the Javascript engine
running on the client side. 


I've decided to keep all the code in this one python file because this way it 
will be easy to distribute the CLI by just copying this one file to the machine
you're going to have your JSDB clients connect to.


Setting up your webpage
-----------------------

To use the jsdb debugger you must include the jsdb.js script from your HTML 
with a simple script inclusion like so:

<script type="text/javascript" src="jsdb.js"></script>

Now before you do that you should also make sure you've started up the jsdb
command line tool so that it can receive connections form the various pages
that will be debuggable. By default the jsdb command line too will listen on 
localhost at port 2222


Starting the JSDB CLI tool
--------------------------



"""
import sys
import time
import readline
import threading
import json

from twisted.internet import reactor
from autobahn.websocket import WebSocketServerFactory, WebSocketServerProtocol
        
global jscnt
jscnt = 0

global clireader
clireader = None

global PORT
PORT = 22222

global factory
factory = None
connections = {}
PROMPT = '> '

def logline(msg):
    sys.stdout.write("\n%s\n%s" % (msg, PROMPT))
    sys.stdout.flush()

class WebSocketHandler(WebSocketServerProtocol): 

    def onClose(self, wasClean, code, reason):
#        logline("ONCLOSE: %s" % reason)
        WebSocketServerProtocol.onClose(self, wasClean, code, reason)
        delkey = None
        for key in connections:
            if connections[key]['wsh'] == self:
                delkey = key
        if delkey:
            del connections[delkey]
            logline("jsdb client %s disconnected." % delkey)
    
    def onMessage(self, msg, binary):
        global jscnt
#        logline("ONMESSAGE: %s" % msg)
        msg = eval(msg)
        
        # on register we actualy put this new connection into the 
        # the currently handle open connections
        if msg['cmd'] == "register":
            client = msg['id']['client']
            key = "%s:%d" % (client['url'], client['ctime'])
            connections['js%d' % jscnt] = { 'from': key, 'wsh': self }
            logline("jsdb client js%d connected from %s" % (jscnt,client))
            jscnt = jscnt + 1
        elif msg['cmd'] == "unregister":
            key = "%s:%d" % (client['url'], client['ctime'])
            del connections[key] 
            logline("jsdb client %s disconnected." % key)
        elif msg['cmd'] == "resp":
            global clireader
            clireader.resp = msg['data']
            clireader.lock.acquire()
            clireader.lock.notify()
            clireader.lock.release()
        elif msg['cmd'] == "heartbeat":
            pass
#            logline('heartbeat from %s' % msg['from'])

class CLIReader(threading.Thread):

    running = True
    jsclient = None
    execid = 0
    lock = threading.Condition()

    def exit(self,args):
        global factory
        self.running = False
    
    def help(self,args):
        pass

    def list(self,args):
        print("connected jsdb clients\n")
        cnt = 0
        for jsid in connections:
            print(" * %s -> %s" % (jsid,connections[jsid]['from']))
            cnt = cnt + 1
        print('')

    def js(self,args):
        if not(self.jsclient):
            print("you're not connected to any jsdb client.")
            return


    def join(self,args):
        if len(args) == 0:
            print("you need to specify a client id")
            return

        jsid = args[0]

        if jsid in connections:
            global PROMPT
            global clireader
            
            jsclient = connections[jsid]
            self.jsclient = jsclient['wsh']
            PROMPT = '%s> ' % jsid
            print('connected to %s' % jsid)
            print("to disconnect type //exit")
            print("all commands are executed on the client")
            
            line = raw_input("> ")

            while (line != "//exit" ):
                javascript = json.dumps({'execid': self.execid , 'js':line})
                self.execid = self.execid + 1

                clireader.resp = None
                self.lock.acquire()
                self.jsclient.sendMessage(javascript)

                # wait for response otherwise timeout after 10s
                self.lock.wait(10000)
                self.lock.release()

                if clireader.resp:
                    print(clireader.resp['info'])
                    clireader.resp = None
                else:
                    print("timed out waiting for response...")

                line = raw_input("> ")
        else:
             print("unknown jsclient %s" % jsid)

    def disconnect(self,args):
        global PROMPT
        self.jsclient = None
        PROMPT = '> '
        print('disconnected')

    def run(self):
        global factory

        def completer(text, state):
            values = { 'help', 'list', 'join', 'exit' }
            matches = [ value for value in values if text in value ]

            try:
                return matches[state]
            except IndexError:
                return None

        readline.set_completer(completer)
        readline.parse_and_bind('tab: complete')

        try:
            print('jsdb started')
            while self.running:
                line = raw_input(PROMPT)

                if len(line) == 0:
                    continue

                # now execute the command that was passed
                cmd = line.split(' ')
                if cmd[0] in dir(self): 
                    getattr(self,cmd[0])(cmd[1:])
                else:
                    print("unknown cmd %s" % cmd[0])
        finally:
            # very important to call the stop from the same thread that 
            # created the actual reactor server
            reactor.callFromThread(reactor.stop)

if __name__ == '__main__':
    clireader = CLIReader()
    clireader.start()

    factory = WebSocketServerFactory()
    factory.protocol = WebSocketHandler
    reactor.listenTCP(PORT, factory)
    print('JSDB debugger listening at %d' % PORT)
    reactor.run()

