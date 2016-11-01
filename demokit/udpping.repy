# Handle an incoming message
def got_reply(srcip,srcport,mess,ch):
  print "received message: '"+mess+"' from "+srcip+":"+str(srcport)

if callfunc == 'initialize':
  if len(callargs) != 2:
    raise Exception("Must specify 'IP port' to send a ping packet")

  myip = getmyip()

  print "My IP is:",myip
  print "Sending a ping message to:",callargs[0],"port",callargs[1]

  # my port is a command line arg
  recvmess(myip,int(callargs[1]),got_reply)  
  sendmess(callargs[0],int(callargs[1]),"Ping message from:"+getmyip()+":"+str(callargs[1]), myip,int(callargs[1]))
  # exit in five seconds
  settimer(5,exitall,())
  

