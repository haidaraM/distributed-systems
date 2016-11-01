"""
<Program Name>
  clearinghouse/clearinghouse.py

<Purpose>
  Provides functions to interact with the Clearinghouse.
  
  module_level_help contains instructions on how to use this module from the
  seash command line.
  
"""

import command_callbacks


module_level_help = """
Clearinghouse Module

This module contains commands that allow you to interact with the Seattle 
Clearinghouse.  Specifically, it provides functionality for acquiring and
releasing vessels.

To acquire vessels, use the 'get' command:
  user@ !> get 3

To release vessels, use the 'release' command.
  user@ !> 

"""


get_helptext = """
get # [type]

Connects to the Clearinghouse and acquires vessels.  The identity specified
must have a private key loaded.

guest0@ !> get 3 wan
['129.97.74.14:1224']
Added targets: %1(129.97.74.14:1224:v10), %2(129.97.74.14:1224:v4), %3(129.97.74.14:1224:v6)
Added group 'acquired' with 3 targets
"""

release_helptext = """
release [group]

Releases the vessels belonging to the specified identity.  The vessels must be owned by the
default identity.  If the groupname is omitted, the current group is released.

guest0@ !> browse
['129.97.74.14:1224']
Added targets: %1(129.97.74.14:1224:v10), %2(129.97.74.14:1224:v4), %3(129.97.74.14:1224:v6)
Added group 'browsegood' with 3 targets
guest0@ !> release browsegood
guest0@ !> on browsegood list
guest0@ !>

"""

command_dict = {
  # get # [type]
  'get':{ 'name':'get', 'callback': None,
             'summary': "Acquires vessels", 'example': "# [type]",
             'help_text': get_helptext, 'children': {
      '[ARGUMENT]': { 'name':'vesselcount', 'callback': command_callbacks.get, 'children':{
          'wan': { 'name':'type', 'callback': command_callbacks.get, 'children':{}},
          'lan': { 'name':'type', 'callback': command_callbacks.get, 'children':{}},
          'nat': { 'name':'type', 'callback': command_callbacks.get, 'children':{}},}},}},

  # release group
  'release': { 'name':'release', 'callback': command_callbacks.release,
               'summary': "Releases a group of vessels", 'example': "group",
               'help_text': release_helptext, 'children': {
      '[GROUP]': {'name':'groupname', 'callback': command_callbacks.release_args, 'children': {}}}}
}

moduledata = {
  'command_dict': command_dict,
  'help_text': module_level_help,
  'url': None,
}