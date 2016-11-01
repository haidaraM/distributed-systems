"""
Author: Alan Loh
Module: Holds all non-callback seash-related methods here.

This would include:
-Helper functions
-Functions that operate on a target
"""

###Helper Methods###

import seash_global_variables

import seash_exceptions

import repyhelper

#repyhelper.translate_and_import("nmclient.repy")
import fastnmclient

# Use local clock for time if there is no network connectivity
import time

repyhelper.translate_and_import("time.repy")

repyhelper.translate_and_import("rsa.repy")

repyhelper.translate_and_import("listops.repy")

repyhelper.translate_and_import("parallelize.repy")

repyhelper.translate_and_import("domainnameinfo.repy")

repyhelper.translate_and_import("advertise.repy")   #  used to do OpenDHT lookups

repyhelper.translate_and_import("geoip_client.repy") # used for `show location`

repyhelper.translate_and_import("serialize.repy") # used for loadstate and savestate



def update_time():
  """
  <Purpose>
    Updates the time that is used internally for nodemanager communications.

  <Arguments>
    None

  <Side Effects>
    Updates the time within time.repy.
    If there is no network connection, the local clock is used.

  <Exceptions>
    None

  <Returns>
    None
  """
  # Since we import time.repy, we will only use the local clock if none of
  # the default time servers respond.
  time_register_method('local', local_updatetime)
  time_updatetime(34612)



def local_updatetime(port):
  """
  <Purpose>
    Callback for time_interface.repy to update the time that is used
    internally for nodemanager communications.

  <Arguments>
    port:
        The port to update on.  This is not used however.  It is only
        specified to adhere to the function signature expected by
        time_interface.repy.

  <Side Effects>
    If we reach this function, then it means that other time server updates
    failed.  We will notify the user of the failure, and set time.repy to
    use the local clock.

  <Exceptions>
    None

  <Returns>
    None
  """
  print 'Time update failed, could not connect to any time servers...'
  print 'Your network connection may be down.'
  print "Falling back to using your computer's local clock."
  print

  # time.time() gives us the # of seconds since 1970, whereas the NTP
  # services gives us the # of seconds since 1900.
  time_settime(time.time() + time_seconds_from_1900_to_1970)



# Saves the current state to file. Helper method for the savestate
# command. (Added by Danny Y. Huang)
def savestate(statefn, handleinfo, host, port, expnum, filename, cmdargs,
              defaulttarget, defaultkeyname, autosave, currentkeyname):

  # obtain the handle info dictionary
  for longname in seash_global_variables.vesselinfo.keys():
    vessel_handle = seash_global_variables.vesselinfo[longname]['handle']
    handleinfo[longname] = fastnmclient.nmclient_get_handle_info(vessel_handle)


  state = {}
  state['targets'] = seash_global_variables.targets
  state['keys'] = seash_global_variables.keys
  state['vesselinfo'] = seash_global_variables.vesselinfo
  state['nextid'] = seash_global_variables.nextid
  state['handleinfo'] = handleinfo
  state['host'] = host
  state['port'] = port
  state['expnum'] = expnum
  state['filename'] = filename
  state['cmdargs'] = cmdargs
  state['defaulttarget'] = defaulttarget
  state['defaultkeyname'] = defaultkeyname
  state['autosave'] = autosave
  state['globalseashtimeout'] = seash_global_variables.globalseashtimeout
  state['globaluploadrate'] = seash_global_variables.globaluploadrate


  # serialize states and encrypt
  if seash_global_variables.keys.has_key(defaultkeyname):
    cypher = rsa_encrypt(serialize_serializedata(state), seash_global_variables.keys[currentkeyname]['publickey'])
  else:
    raise seash_exceptions.UserError("The keyname '" + defaultkeyname + "' is not loaded.")


  # writing encrypted serialized states to file
  # Exceptions are caught outside of the method
  try:
    state_obj = open(statefn, 'w')
    state_obj.write(cypher)
  finally:
    state_obj.close()



def is_immutable_targetname(targetname):
  if targetname.startswith('%') or ':' in targetname:
    return True
  return False


def valid_targetname(targetname):
  if targetname.startswith('%') or ':' in targetname or ' ' in targetname:
    return False
  return True


def fit_string(stringdata, length):
  if len(stringdata) > length:
    return stringdata[:length-3]+'...'
  return stringdata


nextidlock = getlock()
def atomically_get_nextid():

  # mutex around getting an id
  nextidlock.acquire()

  myid = seash_global_variables.nextid
  seash_global_variables.nextid = seash_global_variables.nextid + 1

  nextidlock.release()

  return myid



# adds a vessel and returns the new ID...
def add_vessel(longname, keyname, vesselhandle):

  seash_global_variables.vesselinfo[longname] = {}
  seash_global_variables.vesselinfo[longname]['handle'] = vesselhandle
  seash_global_variables.vesselinfo[longname]['keyname'] = keyname
  seash_global_variables.vesselinfo[longname]['IP'] = longname.split(':')[0]
  seash_global_variables.vesselinfo[longname]['port'] = int(longname.split(':')[1])
  seash_global_variables.vesselinfo[longname]['vesselname'] = longname.split(':')[2]
  # miscelaneous information about the vessel (version, nodeID, etc.)
  seash_global_variables.vesselinfo[longname]['information'] = {}

  # set up a reference to myself...
  seash_global_variables.targets[longname] = [longname]

  myid = atomically_get_nextid()

  # add my id...
  seash_global_variables.targets['%'+str(myid)] = [longname]
  seash_global_variables.vesselinfo[longname]['ID'] = '%'+str(myid)

  # add me to %all...
  seash_global_variables.targets['%all'].append(longname)

  return myid




def copy_vessel(longname, newvesselname):

  newhandle = fastnmclient.nmclient_duplicatehandle(seash_global_variables.vesselinfo[longname]['handle'])
  newlongname = seash_global_variables.vesselinfo[longname]['IP']+":"+str(seash_global_variables.vesselinfo[longname]['port'])+":"+newvesselname
  add_vessel(newlongname,seash_global_variables.vesselinfo[longname]['keyname'],newhandle)
  return newlongname




def delete_vessel(longname):

  # remove the item...
  del seash_global_variables.vesselinfo[longname]

  # remove the targets that reference it...
  for target in seash_global_variables.targets.copy():

    # if in my list...
    if longname in seash_global_variables.targets[target]:

      # if this is the %num entry or longname entry...
      if ('%' in target and target != '%all') or longname == target:
        del seash_global_variables.targets[target]
        continue

      # otherwise remove the item from the list...
      seash_global_variables.targets[target].remove(longname)




def longnamelist_to_nodelist(longnamelist):

  retlist = []
  for longname in longnamelist:
    nodename = seash_global_variables.vesselinfo[longname]['IP']+":"+str(seash_global_variables.vesselinfo[longname]['port'])
    retlist.append(nodename)

  return retlist




def find_handle_for_node(nodename):

  for longname in seash_global_variables.vesselinfo:
    if longname.rsplit(':',1)[0] == nodename:
      return seash_global_variables.vesselinfo[longname]['handle']

  raise IndexError("Cannot find handle for '"+nodename+"'")





#################### functions that operate on a target

MAX_CONTACT_WORKER_THREAD_COUNT = 10


# This function abstracts out contacting different nodes.   It spawns off
# multiple worker threads to handle the clients...
# by a threaded model in the future...
# NOTE: entries in targetlist are assumed by me to be unique
def contact_targets(targetlist, func,*args):

  phandle = parallelize_initfunction(targetlist, func, MAX_CONTACT_WORKER_THREAD_COUNT, *args)

  while not parallelize_isfunctionfinished(phandle):
    sleep(.1)

  # I'm going to change the format slightly...
  resultdict = parallelize_getresults(phandle)

  # There really shouldn't be any exceptions in any of the routines...
  if resultdict['exception']:
    print "WARNING: ",resultdict['exception']

  # I'm going to convert the format to be targetname (as the key) and
  # a value with the return value...
  retdict = {}
  for nameandretval in resultdict['returned']:
    retdict[nameandretval[0]] = nameandretval[1]

  return retdict




# This function abstracts out contacting different nodes.   It is obsoleted by
# the threaded model...   This code is retained for testing reasons only
def simple_contact_targets(targetlist, func,*args):

  retdict = {}

  # do the function on each target, returning a dict of results.
  for target in targetlist:
    retdict[target] = func(target,*args)

  return retdict




# used in show files
def showfiles_target(longname):

  vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

  try:
    filedata = fastnmclient.nmclient_signedsay(seash_global_variables.vesselinfo[longname]['handle'],"ListFilesInVessel",vesselname)

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    return (True, filedata)








# used in show log
def showlog_target(longname):

  vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

  try:
    logdata = fastnmclient.nmclient_signedsay(seash_global_variables.vesselinfo[longname]['handle'],"ReadVesselLog",vesselname)

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    return (True, logdata)





# used in show resources
def showresources_target(longname):

  vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

  try:
    resourcedata = fastnmclient.nmclient_rawsay(seash_global_variables.vesselinfo[longname]['handle'],"GetVesselResources",vesselname)

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    return (True, resourcedata)


# used in show offcut
def showoffcut_target(nodename):

  vesselhandle = find_handle_for_node(nodename)

  try:
    offcutdata = fastnmclient.nmclient_rawsay(vesselhandle,"GetOffcutResources")

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    return (True, offcutdata)





def browse_target(node, currentkeyname, targetgroup='browsegood'):

  # NOTE: I almost think I should skip those nodes that I know about from
  # previous browse commands.   Perhaps I should have an option on the browse
  # command?

  host, portstring = node.split(':')
  port = int(portstring)

  # get information about the node's vessels
  try:
    nodehandle = fastnmclient.nmclient_createhandle(host, port,
                                       privatekey = seash_global_variables.keys[currentkeyname]['privatekey'],
                                       publickey = seash_global_variables.keys[currentkeyname]['publickey'],
                                       timeout=seash_global_variables.globalseashtimeout)

  except fastnmclient.NMClientException,e:
    return (False, str(e))

  try:
    # need to contact the node to get the list of vessels we can perform
    # actions on...
    ownervessels, uservessels = fastnmclient.nmclient_listaccessiblevessels(nodehandle,seash_global_variables.keys[currentkeyname]['publickey'])

    retlist = []

    # we should add anything we can access (whether a user or owner vessel)
    for vesselname in ownervessels + uservessels:
      longname = host+":"+str(port)+":"+vesselname

      # if we haven't discovered the vessel previously...
      if longname not in seash_global_variables.targets:
        # set the vesselname in the handle
        newhandle = fastnmclient.nmclient_duplicatehandle(nodehandle)
        handleinfo = fastnmclient.nmclient_get_handle_info(newhandle)
        handleinfo['vesselname'] = vesselname
        fastnmclient.nmclient_set_handle_info(newhandle, handleinfo)

        # then add the vessel to the target list, etc.
        # add_vessel has no race conditions as long as longname is unique
        # (and it should be unique)
        id = add_vessel(longname,currentkeyname,newhandle)
        seash_global_variables.targets[targetgroup].append(longname)

        # and append some information to be printed...
        retlist.append('%'+str(id)+"("+longname+")")



  finally:
    fastnmclient.nmclient_destroyhandle(nodehandle)

  return (True, retlist)


def list_or_update_target(longname):

  vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

  try:
    vesseldict = fastnmclient.nmclient_getvesseldict(seash_global_variables.vesselinfo[longname]['handle'])

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    # updates the dictionary of our node information (dictionary used in show,
    # etc.)
    for key in vesseldict['vessels'][vesselname]:
      seash_global_variables.vesselinfo[longname][key] = vesseldict['vessels'][vesselname][key]

    # Update the "information" (version number, etc.)
    del vesseldict['vessels']
    seash_global_variables.vesselinfo[longname]['information'] = vesseldict

    return (True,)




def upload_target(longname, remotefn, filedata):

  vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

  try:
    # add the file data...
    fastnmclient.nmclient_signedsay(seash_global_variables.vesselinfo[longname]['handle'], "AddFileToVessel", vesselname, remotefn, filedata)

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    return (True,)




def download_target(longname,localfn,remotefn):

  vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

  try:
    # get the file data...
    retrieveddata = fastnmclient.nmclient_signedsay(seash_global_variables.vesselinfo[longname]['handle'], "RetrieveFileFromVessel", vesselname, remotefn)

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    writefn = localfn+"."+longname.replace(':','_')
    # write to the local filename (replacing ':' with '_')...
    fileobj = open(writefn,"w")
    fileobj.write(retrieveddata)
    fileobj.close()
    # for output...
    return (True, writefn)



def cat_target(longname,remotefn):

  vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

  try:
    # get the file data...
    retrieveddata = fastnmclient.nmclient_signedsay(seash_global_variables.vesselinfo[longname]['handle'], "RetrieveFileFromVessel", vesselname, remotefn)

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    # and return it..
    return (True, retrieveddata)



def delete_target(longname,remotefn):

  vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

  try:
    # delete the file...
    fastnmclient.nmclient_signedsay(seash_global_variables.vesselinfo[longname]['handle'], "DeleteFileInVessel", vesselname, remotefn)

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    return (True,)




def start_target(longname, argstring):

  vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

  try:
    # start the program
    fastnmclient.nmclient_signedsay(seash_global_variables.vesselinfo[longname]['handle'], "StartVessel", vesselname, argstring)

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    return (True,)




def stop_target(longname):

  vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

  try:
    # stop the programs
    fastnmclient.nmclient_signedsay(seash_global_variables.vesselinfo[longname]['handle'], "StopVessel", vesselname)

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    return (True,)




def reset_target(longname):

  vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

  try:
    # reset the target
    fastnmclient.nmclient_signedsay(seash_global_variables.vesselinfo[longname]['handle'], "ResetVessel", vesselname)

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    return (True,)




def run_target(longname,filename,filedata, argstring):

  vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

  try:
    fastnmclient.nmclient_signedsay(seash_global_variables.vesselinfo[longname]['handle'], "AddFileToVessel", vesselname, filename, filedata)
    fastnmclient.nmclient_signedsay(seash_global_variables.vesselinfo[longname]['handle'], "StartVessel", vesselname, argstring)

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    return (True,)




# didn't test...
def split_target(longname, resourcedata):

  vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

  try:
    newvesselnames = fastnmclient.nmclient_signedsay(seash_global_variables.vesselinfo[longname]['handle'], "SplitVessel", vesselname, resourcedata)

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    newname1 = copy_vessel(longname, newvesselnames.split()[0])
    newname2 = copy_vessel(longname, newvesselnames.split()[1])
    delete_vessel(longname)
    return (True,(newname1,newname2))




# didn't test...
def join_target(nodename,nodedict):

  if len(nodedict[nodename]) < 2:
    # not enough vessels, nothing to do
    return (False, None)


  # I'll iterate through the vessels, joining one with the current
  # (current starts as the first vessel and becomes the "new vessel")
  currentvesselname = seash_global_variables.vesselinfo[nodedict[nodename][0]]['vesselname']
  currentlongname = nodedict[nodename][0]

  # keep a list of what I replace...
  subsumedlist = [currentlongname]

  for longname in nodedict[nodename][1:]:
    vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

    try:
      newvesselname = fastnmclient.nmclient_signedsay(seash_global_variables.vesselinfo[longname]['handle'], "JoinVessels", currentvesselname, vesselname)

    except fastnmclient.NMClientException, e:
      return (False, str(e))

    else:
      newname = copy_vessel(longname, newvesselname)
      delete_vessel(longname)
      delete_vessel(currentlongname)
      subsumedlist.append(longname)
      currentlongname = newname
      currentvesselname = newvesselname


  else:
    return (True, (currentlongname,subsumedlist))




# didn't test...
def setowner_target(longname,newowner):

  vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

  try:
    fastnmclient.nmclient_signedsay(seash_global_variables.vesselinfo[longname]['handle'], "ChangeOwner", vesselname, rsa_publickey_to_string(seash_global_variables.keys[newowner]['publickey']))

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    return (True,)




# didn't test...
def setadvertise_target(longname,newadvert):

  vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

  try:
    # do the actual advertisement changes
    fastnmclient.nmclient_signedsay(seash_global_variables.vesselinfo[longname]['handle'], "ChangeAdvertise", vesselname, newadvert)

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    return (True,)




def setownerinformation_target(longname,newownerinformation):

  vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

  try:
    # do the actual advertisement changes
    fastnmclient.nmclient_signedsay(seash_global_variables.vesselinfo[longname]['handle'], "ChangeOwnerInformation", vesselname, newownerinformation)

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    return (True,)




def setusers_target(longname,userkeystring):

  vesselname = seash_global_variables.vesselinfo[longname]['vesselname']

  try:
    fastnmclient.nmclient_signedsay(seash_global_variables.vesselinfo[longname]['handle'], "ChangeUsers", vesselname, userkeystring)

  except fastnmclient.NMClientException, e:
    return (False, str(e))

  else:
    return (True,)




# Checks if both keys are setup
def check_key_set(name):

  if (name in seash_global_variables.keys and 'publickey' in seash_global_variables.keys[name] and 'privatekey' in seash_global_variables.keys[name] and seash_global_variables.keys[name]['publickey'] and seash_global_variables.keys[name]['privatekey']):

    if not check_key_pair_compatibility(name):
      raise seash_exceptions.UserError("Error: Mis-matched Public/Private key pair!")




# Check the keys to make sure they are compatible, for the given name
def check_key_pair_compatibility(name):

    # Check for both sets of keys
    setPublic = seash_global_variables.keys[name]['publickey']
    setPrivate = seash_global_variables.keys[name]['privatekey']

    # Check for a mis-match
    match = rsa_matching_keys(setPrivate, setPublic)

    return match


# Reload the handles of a node. Used when "loadstate" is invoked. Returns a
# tuple (success, e), where success is a boolean and e is a string of error
# messages. Added by Danny Y. Huang.
def reload_target(longname, handleinfo):

  host, portstring, vesselname = longname.split(':')
  port = int(portstring)

  try:
    priKey = handleinfo[longname]['privatekey']
    pubKey = handleinfo[longname]['publickey']

  except KeyError:
    error = ("Vessel is absent in the handleinfo dictionary.")
    return (False, error)

  # find the user who has these keys
  thiskeyname = ""

  for keyname in seash_global_variables.keys.keys():
    if (seash_global_variables.keys[keyname]['publickey'] == pubKey and
        seash_global_variables.keys[keyname]['privatekey'] == priKey):
      thiskeyname = keyname
      break

  if not thiskeyname:
    return (False, "User with keyname '" + keyname + "' is not found.")

  # create new handle for the vessel
  try:
    vessel_handle = fastnmclient.nmclient_createhandle(host, port, privatekey = priKey, publickey = pubKey, timeout=seash_global_variables.globalseashtimeout)

  except fastnmclient.NMClientException, error:
    return (False, str(error))


  try:
    fastnmclient.nmclient_set_handle_info(vessel_handle, handleinfo[longname])
    seash_global_variables.vesselinfo[longname]['handle'] = vessel_handle

    # hello test to see if the vessel is available
    (ownervessels, uservessels) = fastnmclient.nmclient_listaccessiblevessels(vessel_handle, pubKey)
    if not (ownervessels + uservessels):
      return (False, "Vessel is not available for keyname " + keyname + ".")

  except Exception, error:
    # Catching unexpected exceptions
    return (False, "General exception: " + str(error) + ".")

  return (True, "")




# Determines if there's a need to temporarily change the vessel timeout
# to avoid timing out on bad connection speeds when uploading file.
def set_upload_timeout(filedata):

  filesize = len(filedata)
  est_upload_time = filesize / seash_global_variables.globaluploadrate

  # sets the new timeout if necessary
  if est_upload_time > seash_global_variables.globalseashtimeout:

    for longname in seash_global_variables.vesselinfo:
      thisvesselhandle = seash_global_variables.vesselinfo[longname]['handle']
      thisvesselhandledict = fastnmclient.nmclient_get_handle_info(thisvesselhandle)
      thisvesselhandledict['timeout'] = est_upload_time
      fastnmclient.nmclient_set_handle_info(thisvesselhandle,thisvesselhandledict)




# Resets each vessel's timeout to the value of globalseashtimeout
def reset_vessel_timeout():

  # resets each vessel's timeout to the original values before file upload
  for longname in seash_global_variables.vesselinfo:
    thisvesselhandle = seash_global_variables.vesselinfo[longname]['handle']
    thisvesselhandledict = fastnmclient.nmclient_get_handle_info(thisvesselhandle)
    thisvesselhandledict['timeout'] = seash_global_variables.globalseashtimeout
    fastnmclient.nmclient_set_handle_info(thisvesselhandle,thisvesselhandledict)





def print_vessel_errors(retdict):
  """
  <Purpose>
    Prints out any errors that occurred while performing an action on vessels,
    in a human readable way.

    Errors will be printed out in the following format:
    description [reason]
    Affected vessels: nodelist

    To define a new error, add the following entry to ERROR_RESPONSES in this
    function:
      'error_identifier': {
        'error': 'description for the error',
        'reason': 'reason for the error' (optional).
    'error_identifier'
      This is the substring of the error that can be used to identify it.
      Longer identifiers will have a higher priority over shorter identifiers.
      For example, authentication errors could be identified using the string
      'Insufficient Permissions'.
    'error'
      This is where you put the description for the error to show to the user.
    'reason' (optional)
      This is where you put clarification for the error to ease the user.
      Additionally, you may put things that they could do to fix the error here,
      if applicable. If you don't want to show a reason, don't include this key
      in the dictionary.
      Examples when you would not put a reason is if you received a timeout,
      since the user can't do anything to fix them.

  <Arguments>
    retdict:
      A list of longnames mapped against a tuple (Success?, Message/Errortext).

  <Side Effects>
    Prints error messages onto the screen. See documentation for ERROR_RESPONSES
    for more information.

  <Exceptions>
    Exception

  <Return>
    None

  """
  ERROR_RESPONSES = {
    "Node Manager error 'Insufficient Permissions'": {
      'error': "You lack sufficient permissions to perform this action.",
      'reason': "Did you release the resource(s) by accident?"},
    'timed out': {
      'error':'Connection timed out.'},
    "file not found": {
      'error': "The specified file(s) could not be found.",
      'reason': "Please check the filename."},
    }

  # A dictionary mapping error identifiers to a list of vessels that share
  # that error.
  error_longnames = {}

  for longname in retdict:
    # if the first item is true, then there is no error.
    if not retdict[longname][0]:
      matches = []
      # Loop until we find the response
      for error_string in ERROR_RESPONSES:
        if error_string.lower() in retdict[longname][1].lower():
          # This is the first match
          if not matches:
            matches = [error_string]
          else:
            # This is a better match, forget about the previous matches
            if len(error_string) > len(matches[0]):
              matches = [error_string]

            elif len(error_string) == len(matches[0]):
              matches.append(error_string)

      # If there isn't a match, use the error string as an error identifier
      if not matches:
        errorid = retdict[longname][1]

      else:
        # There should not be more than 1 match for any error.
        # If there is, log the error to a file.
        if len(matches) != 1:
          errfile = open('seasherrors.txt', 'a')
          errorstring = "Multiple matches with same priority:" + '\n'.join(matches)
          errfile.write(errorstring)
          errfile.close()
          raise Exception(errorstring)
        errorid = matches[0]

      # Create the longname list if it doesn't already exist
      if errorid not in error_longnames:
        error_longnames[errorid] = []
      error_longnames[errorid].append(longname)


  # Print the errors out
  for errorid in error_longnames:
    # Represent the list of nodes in a human readable way.
    nodestring = ''
    for node in error_longnames[errorid]:
      # This is the first node
      if node == error_longnames[errorid][0]:
        divider = ''
      # This is a node in the middle
      elif node != error_longnames[errorid][-1]:
        divider = ', '
      # This is the last node
      else:
        # We will always have at least 2 nodes at this point, since if there
        # is only one node, it will be treated as the first node. Therefore,
        # we only have two cases, where there are exactly 2 nodes, or more than
        # 2 nodes.
        # If we have two nodes, we want: "node_1 and node_2".
        # Otherwise, we want: "node_1, node_2, ..., and node_n".
        divider = " and "
        if len(error_longnames[errorid]) > 2:
          divider = ',' + divider
      nodestring += divider + node

    if errorid in ERROR_RESPONSES:
      print ERROR_RESPONSES[errorid]['error'],
      if 'reason' in ERROR_RESPONSES[errorid]:
        print ERROR_RESPONSES[errorid]['reason']
      else:
        # Caret is still on the same line as the list of nodes
        print
    else:
      # Unknown error.
      print "An error occurred: " + errorid
    print "Affected vessels:", nodestring + '.'


def get_commands_from_commanddict(commanddict):
  """
  <Purpose>
    Extracts the commands that are contained in the command dictionary.
    The arguments of these commands are not included.

  <Arguments>
    commanddict: A command dictionary in the format specified in
      seash_dictionary.

  <Exceptions>
    None

  <Side Effects>
    None

  <Return>
    A list of commands that are in the commanddict.
  """
  if not commanddict:
    return []

  commands = []
  for command in commanddict:
    has_user_argument = False
    subcommands = get_commands_from_commanddict(commanddict[command]['children'])
    if subcommands:
      for subcommand in subcommands:
        commands.append(command + " " + subcommand)
    else:
      commands.append(command)
  return commands