"""
<Filename>
  geoip_module.py

<Purpose>
  This is the command dictionary for location-related services for seash.
  For more information on the command dictionary, see the documentation for
  seash_importer.py.
  
  It implements the following commands:  
    show location
    show coordinates

"""

import seash_global_variables
import seash_exceptions
import repyhelper
repyhelper.translate_and_import("geoip_client.repy")


# show location        -- Display location information about the nodes
def show_location(input_dict, environment_dict):

  if not environment_dict['currenttarget']:
    raise seash_exceptions.UserError("Error, command requires a target")

  geoip_init_client()

  # we should only visit a node once...
  printedIPlist = []

  for longname in seash_global_variables.targets[environment_dict['currenttarget']]:
    thisnodeIP = seash_global_variables.vesselinfo[longname]['IP']

    # if we haven't visited this node
    if thisnodeIP not in printedIPlist:
      printedIPlist.append(thisnodeIP)

      try:
        location_dict = geoip_record_by_addr(thisnodeIP)
      except:
        location_dict = None

      if location_dict:
        print str(seash_global_variables.vesselinfo[longname]['ID'])+'('+str(thisnodeIP)+'): '+geoip_location_str(location_dict)
      else:
        print str(seash_global_variables.vesselinfo[longname]['ID'])+'('+str(thisnodeIP)+'): Location unknown'


#show coordinates -- Display the latitude & longitude of the nodes
def show_coordinates(input_dict, environment_dict):

  if not environment_dict['currenttarget']:
    raise seash_exceptions.UserError("Error, command requires a target")

  geoip_init_client()

  # we should only visit a node once...
  printedIPlist = []

  for longname in seash_global_variables.targets[environment_dict['currenttarget']]:
    thisnodeIP = seash_global_variables.vesselinfo[longname]['IP']

    # if we haven't visited this node
    if thisnodeIP not in printedIPlist:
      printedIPlist.append(thisnodeIP)
      location_dict = geoip_record_by_addr(thisnodeIP)

      if location_dict:
        print str(seash_global_variables.vesselinfo[longname]['ID'])+'('+str(thisnodeIP)+'): ' + str(location_dict['latitude']) + ", " + str(location_dict['longitude'])

      else:
        print str(seash_global_variables.vesselinfo[longname]['ID'])+'('+str(thisnodeIP)+'): Location unknown'


SHOW_LOCATION_HELPTEXT = """
show location

Uses a geo-IP location service to return information about the position of the
nodes in the current group.

Example:
exampleuser@browsegood !> show ip
192.x.x.2
193.x.x.42
219.x.x.62
exampleuser@browsegood !> show location
%1(192.x.x.2): Location unknown
%3(193.x.x.42): Cesson-svign, France
%4(219.x.x.62): Beijing, China

"""

SHOW_COORDINATES_HELPTEXT = """
show coordinates

Uses a geo-IP location service to get approximate latitude and longitude
information about nodes in the current group.

Example:
exampleuser@browsegood !> show location
%1(192.x.x.2): Location unknown
%3(193.x.x.42): Cesson-svign, France
%4(219.x.x.62): Beijing, China
exampleuser@browsegood !> show coordinates
%1(192.x.x.2): Location unknown
%3(193.x.x.42): 48.1167, 1.6167
%4(219.x.x.62): 39.9289, 116.3883

"""

command_dict = {
  'show':{
    'children': {
      'location':{
      'name':'location',
      'callback': show_location,
      'summary': "Display location information (countries) for the nodes",
      'help_text':SHOW_LOCATION_HELPTEXT,
      'children': {}},
    'coordinates':{
      'name':'coordinates',
      'callback': show_coordinates,
      'summary':'Display the latitude & longitude of the node',
      'help_text':SHOW_COORDINATES_HELPTEXT,
      'children': {}}
    }}
}


help_text = """
GeoIP Module

This module includes commands that provide information regarding vessels' 
geographical locations.  To get started using this module, acquire several 
vessels through the Seattle Clearinghouse, use the 'browse' command, and then 
in any group, run either 'show location' or 'show coordinates'.
"""


# This is where the module importer loads the module from
moduledata = {
  'command_dict': command_dict,
  'help_text': help_text,
  'url': None,
}