"""
<Program Name>
  clearinghouse/command_callbacks.py

<Purpose>
  Defines all the command callbacks that are used for the Clearinghouse module.

  For more information on how the functions within this module are defined,
  refer to the main command_callbacks.py in the same directory as seash.py.

"""
import seash_helper
import seash_exceptions
import seash_global_variables

import fastnmclient
import seattleclearinghouse_xmlrpc

import repyhelper
repyhelper.translate_and_import('rsa.repy')


is_printed_m2crypto_not_installed = False



# get # [type]
def get(input_dict, environment_dict):
  """
  <Purpose>
    Gets the specified vessels.

  <Arguments>
    input_dict:  The commanddict representing the user's input.
    environment_dict:  The dictionary representing the current seash
                       environment.

  <Side Effects>
    Connects to the Clearinghouse and acquires vessels.
    Adds the acquired vessels to the list of valid targets.

  <Exceptions>
    None

  <Returns>
    None
  """

  if environment_dict['currentkeyname'] is None or not seash_global_variables.keys[environment_dict['currentkeyname']]['privatekey']:
    raise seash_exceptions.UserError("Error, must get as an identity with a private key")

  vesselcount = int(_get_user_argument(input_dict, 'vesselcount'))

  try:
    vesseltype = _get_user_argument(input_dict, 'type')
  # User may not have specified a vesseltype
  except IndexError:
    vesseltype = None

  if not vesseltype in ['wan', 'lan', 'nat', None]:
    raise seash_exceptions.UserError("Error, unknown vessel type '"+vesseltype+"'")

  client = _connect_to_clearinghouse(environment_dict['currentkeyname'])

  # Get the vessels!
  try:
    if vesseltype is None:
      vesseldicts = client.acquire_random_resources(vesselcount)
    else:
      vesseldicts = client.acquire_resources(vesseltype, vesselcount)

    _update_targets(vesseldicts, environment_dict)
  except (seattleclearinghouse_xmlrpc.UnableToAcquireResourcesError, seattleclearinghouse_xmlrpc.NotEnoughCreditsError), e:
    print str(e)


# release
def release(input_dict, environment_dict):
  """
  <Purpose>
    Releases the specified vessels.

  <Arguments>
    input_dict:  The commanddict representing the user's input.
    environment_dict:  The dictionary representing the current seash
                       environment.

  <Side Effects>
    Connects to the Clearinghouse and releases vessels.
    Removes the released vessels from the list of valid targets.
    Does not guarantee that all vessels specified are released!

  <Exceptions>
    None

  <Returns>
    None
  """
  # Get the group name to release
  groupname = environment_dict['currenttarget']
  nodelist = seash_global_variables.targets[groupname]

  # Get the Clearinghouse vessel handles for each vessel
  retdict = seash_helper.contact_targets(nodelist, _get_clearinghouse_vessel_handle)

  clearinghouse_vesselhandles = []
  faillist = []
  # parse the output so we can print out something intelligible
  for nodename in retdict:

    if retdict[nodename][0]:
      clearinghouse_vesselhandles.append(retdict[nodename][1])
    else:
      faillist.append(nodename)

  # Release!
  client = _connect_to_clearinghouse(environment_dict['currentkeyname'])
  client.release_resources(clearinghouse_vesselhandles)

  # Remove each vessel from the targets list
  removed_nodehandles = seash_global_variables.targets[groupname][:]
  for handle in removed_nodehandles:
    for target in seash_global_variables.targets:
      if handle in seash_global_variables.targets[target]:
        seash_global_variables.targets[target].remove(handle)


# release group
def release_args(input_dict, environment_dict):
  """
  <Purpose>
    Releases the specified vessels.

  <Arguments>
    input_dict:  The commanddict representing the user's input.
    environment_dict:  The dictionary representing the current seash
                       environment.

  <Side Effects>
    Connects to the Clearinghouse and releases vessels.
    Removes the released vessels from the list of valid targets.
    Does not guarantee that all vessels specified are released!

  <Exceptions>
    None

  <Returns>
    None
  """
  # Get the group name to release
  groupname = _get_user_argument(input_dict, 'groupname')
  nodelist = seash_global_variables.targets[groupname]

  # Get the Clearinghouse vessel handles for each vessel
  retdict = seash_helper.contact_targets(nodelist, _get_clearinghouse_vessel_handle)

  clearinghouse_vesselhandles = []
  faillist = []
  # parse the output so we can print out something intelligible
  for nodename in retdict:

    if retdict[nodename][0]:
      clearinghouse_vesselhandles.append(retdict[nodename][1])
    else:
      faillist.append(nodename)

  # Release!
  client = _connect_to_clearinghouse(environment_dict['currentkeyname'])
  client.release_resources(clearinghouse_vesselhandles)

  # Remove each vessel from the targets list
  removed_nodehandles = seash_global_variables.targets[groupname][:]
  for handle in removed_nodehandles:
    for target in seash_global_variables.targets:
      if handle in seash_global_variables.targets[target]:
        seash_global_variables.targets[target].remove(handle)


def _update_targets(vesseldicts, environment_dict):
  """
  <Purpose>
    Connects to the nodes in the vesseldicts and adds them to the list
    of valid targets.

  <Arguments>
    vesseldicts:
        A list of vesseldicts obtained through
        SeattleClearinghouseClient calls.

  <Side Effects>
    All valid targets that the user can access on the specified nodes
    are added to the list of targets.

  <Exceptions>
    None

  <Returns>
    None
  """
  # Compile a list of the nodes that we need to check
  nodelist = []
  for vesseldict in vesseldicts:
    nodeip_port = vesseldict['node_ip']+':'+str(vesseldict['node_port'])
    if not nodeip_port in nodelist:
      nodelist.append(nodeip_port)

  # we'll output a message about the new keys later...
  newidlist = []
  faillist = []

  # Clear the list so that the user doesn't target vessels acquired from
  # previous requests when targeting this group
  seash_global_variables.targets['acquired'] = []
  print nodelist

  # currently, if I browse more than once, I look up everything again...
  retdict = seash_helper.contact_targets(
    nodelist,
    seash_helper.browse_target,
    environment_dict['currentkeyname'],
    'acquired')

  # parse the output so we can print out something intelligible
  for nodename in retdict:
    if retdict[nodename][0]:
      newidlist = newidlist + retdict[nodename][1]
    else:
      faillist.append(nodename)

  seash_helper.print_vessel_errors(retdict)

  if len(newidlist) == 0:
    print "Could not add any new targets."
  else:
    print "Added targets: "+", ".join(newidlist)

  if len(seash_global_variables.targets['acquired']) > 0:
    num_targets = str(len(seash_global_variables.targets['acquired']))
    print "Added group 'acquired' with "+num_targets+" targets"


def _get_clearinghouse_vessel_handle(vesselhandle):
  """
  <Purpose>
    Acquires the unique vessel identifier for a given vesselhandle.

  <Arguments>
    vesselhandle:
      A vessel handle expressed in the form node_ip:node_port:vesselname.

  <Side Effects>
    Opens a connection to the vessel to retrieve its nodekey.

  <Exceptions>
    None

  <Returns>
    A list of Clearinghouse vesselhandles for each vessel.

  """
  host, portstring, vesselname = vesselhandle.split(':')
  port = int(portstring)

  # get information about the node's vessels
  try:
    nodehandle = fastnmclient.nmclient_createhandle(host, port,
      timeout=seash_global_variables.globalseashtimeout)

  except fastnmclient.NMClientException,e:
    return (False, str(e))

  try:
    # We need to get the nodekey on this vessel
    vesseldict = fastnmclient.nmclient_getvesseldict(nodehandle)
  except fastnmclient.NMClientException,e:
    return (False, str(e))
  finally:
    fastnmclient.nmclient_destroyhandle(nodehandle)

  nodekeystr = rsa_publickey_to_string(vesseldict['nodekey'])
  return (True, nodekeystr+':'+vesselname)


def _connect_to_clearinghouse(identity):
  global is_printed_m2crypto_not_installed

  try:
    return seattleclearinghouse_xmlrpc.SeattleClearinghouseClient(
        username=identity,
        private_key_string=rsa_privatekey_to_string(
          seash_global_variables.keys[identity]['privatekey']))

  except ImportError:
    # We only want to print this error message on the first time that
    # the user tries to connect to the clearinghouse, so we don't
    # overwhelm the user with unnecessary output.
    if not is_printed_m2crypto_not_installed:
      print "You must have M2Crypto installed to connect to the Clearinghouse securely."
      print "Insecure mode will be used for the rest of this session."
      is_printed_m2crypto_not_installed = True

    return seattleclearinghouse_xmlrpc.SeattleClearinghouseClient(
      username=identity,
      private_key_string=rsa_privatekey_to_string(
        seash_global_variables.keys[identity]['privatekey']),
      allow_ssl_insecure=True)

def _get_user_argument(input_dict, argname):
  # Iterates through the dictionary to retrieve the user's argument
  command_key = input_dict.keys()[0]
  while input_dict[command_key]['name'] is not argname:
     input_dict = input_dict[command_key]['children']
     command_key = input_dict.keys()[0]
  return command_key