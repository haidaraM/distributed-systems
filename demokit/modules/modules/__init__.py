"""
<Program Name>
  modules/__init__.py

<Purpose>
  Provides module manipulation functionality for seash.
  
  module_level_help contains instructions on how to use this module from the
  seash command line.
  
"""


import seash_modules
import seash_dictionary
import seash_helper
import seash_exceptions

# This is where the module callbacks are defined
import command_callbacks


def autocomplete(input_list):
  """
  <Purpose>
    Returns all valid input completions for the specified command line input.
  
  <Arguments>
    input_list: A list of tokens.
  
  <Side Effects>
    None
  
  <Exceptions>
    None
    
  <Returns>
    A list of strings representing valid completions.
  """
  if input_list[0] in ['modulehelp', 'enable', 'disable']:
    commands = []
    for modulename in seash_modules.module_data.keys():
      commands.append(input_list[0] + ' ' + modulename)
    return commands
  return []



module_level_help = """
Modules Module

This module contains commands that pertain to the manipulation of modules.
You can enable/disable modules that are used within seash from here.

To enable a module, use the 'enable' command:
  user@ !> enable variables

To disable a module, use the 'disable' command.
  user@ !> disable variables

You can also view module-level help:
  user@ !> modulehelp variables

And finally, view information on all modules you currently have installed:
  user@ !> show modules

"""


list_all_modules_helptext = """
show modules

Shows information on all installed modules.  Modules will be separated into
two categories: enabled and disabled.  Each entry will be in the following
format:
  [module name] - [URL where the module was installed from, if available]

The URL will be missing if the module was installed manually.


user@ !> show modules
Enabled Modules:
geoip

Installed Modules:
geoip - Install URL not available
selexor - https://seattle.poly.edu/plugins/selexor/
"""

enable_helptext = """
enable [modulename]

Enables use of the specified module.  You can only enable modules if they do
not contain commands that conflict with existing commands.

user@ !> enable modulename
user@ !> enable modulename
Module 'modulename' is already enabled.
user@ !> enable conflictingmodule
Module 'conflictingmodule' cannot be enabled due to these conflicting commands:
show info (default)
get (selexor)
"""

disable_helptext = """
disable [modulename]

Disables the specified module.  You will no longer be able to access the
commands that were found in the disabled module until the module is re-enabled.

Important note:  You cannot disable this module through the disable command.

user@ !> disable modulename
user@ !> disable modulename
Module 'modulename' is not enabled.

"""

modulehelp_helptext = """
help module [modulename]

Displays the module-level help for a particular module.  The module must 
already be installed.

"""

command_dict = {
  # show modules
  'show': {'children': {
      'modules': { 'name': 'modules', 'callback': command_callbacks.list_all_modules,
            'summary': "Shows basic information about all installed modules.",
            'help_text': list_all_modules_helptext, 'children': {}}, }},

  # enable modulename
  'enable':{ 'name':'enable', 'callback': command_callbacks.enable_module,
             'summary': "Enables an installed module", 'example': "[modulename]",
             'help_text': enable_helptext, 'children': {
      '[ARGUMENT]': { 'name':'modulename', 'callback': None, 'children':{}},}},

  # disable modulename
  'disable': { 'name':'disable', 'callback': command_callbacks.disable_module,
               'summary': "Disables an enabled module", 'example': "[modulename]",
               'help_text': disable_helptext, 'children': {
      '[ARGUMENT]': { 'name':'modulename', 'callback': None, 'children':{}},}},

  # modulehelp modulename
  'modulehelp': { 'name': 'modulehelp', 'callback': command_callbacks.print_module_help,
                  'summary': "Shows the module-level helptext for a particular module",
                  'example': '[modulename]', 'help_text': modulehelp_helptext, 
                  'children': {
      '[ARGUMENT]':{ 'name':'modulename', 'callback': None, 'children':{}},}},
}

moduledata = {
  'command_dict': command_dict,
  'help_text': module_level_help,
  'url': None,
  'tab_completer': autocomplete
}