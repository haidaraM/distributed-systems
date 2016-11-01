"""
<Program Name>
  modules/command_callbacks.py

<Purpose>
  Defines all the command callbacks that are used for the modules module.

  For more information on how the functions within this module are defined,
  refer to the main command_callbacks.py in the same directory as seash.py.
  
"""
import seash_modules
import seash_dictionary
import seash_helper
import seash_exceptions

# show modules
def list_all_modules(input_dict, environment_dict):
  """
  <Purpose>
    Lists all installed modules and their status.

  <Arguments>
    input_dict:  The commanddict representing the user's input.
    environment_dict:  The dictionary representing the current seash 
                       environment.

  <Side Effects>
    A list of all enabled modules and all installed modules will be printed to 
    stdout.

  <Exceptions>
    None

  <Returns>
    None
  """
  print "Enabled Modules:"
  print ", ".join(seash_modules.get_enabled_modules())
  print
  print "Installed Modules:"

  # Now print the URLs...
  # Output format:
  # modulename - URL not available  # URL is set to None
  # modulename - https://seattle.poly.edu/seashplugins/modulename/ # URL is set
  for module in seash_modules.module_data:
    print module, '-',
    if seash_modules.module_data[module]['url'] is None:
      print "Install URL not available"
    else:
      print seash_modules.module_data[module]['url']
  print


# enable modulename
def enable_module(input_dict, environment_dict):
  """
  <Purpose>
    Enables an installed module.

  <Arguments>
    input_dict:  The commanddict representing the user's input.
    environment_dict:  The dictionary representing the current seash 
                       environment.

  <Side Effects>
    The module specified in the 'modulename' node will be enabled.

  <Exceptions>
    UserError:  input_dict did not contain a 'modulename' node.

  <Returns>
    None
  """

  # Get the modulename
  dict_mark = input_dict
  try:
    command = dict_mark.keys()[0]
    while dict_mark[command]['name'] != 'modulename':
      dict_mark = input_dict[command]['children']
      command = dict_mark.keys()[0]
    modulename = command
  except IndexError:
    raise seash_exceptions.UserError("Error, command requires a modulename")

  try:
    seash_modules.enable(seash_dictionary.seashcommanddict, modulename)
  except seash_exceptions.ModuleConflictError, e:
    print "Module cannot be imported due to the following conflicting command:"
    print str(e)
  except seash_exceptions.InitializeError, e:
    print "Error while enabling the '"+modulename+"' module."
    seash_modules.disable(seash_dictionary.seashcommanddict, modulename)



def disable_module(input_dict, environment_dict):
  """
  <Purpose>
    Disables an enabled module.

  <Arguments>
    input_dict:  The commanddict representing the user's input.
    environment_dict:  The dictionary representing the current seash 
                       environment.

  <Side Effects>
    The module specified in the 'modulename' node will be enabled.

  <Exceptions>
    UserError:
      input_dict did not contain a 'modulename' node, or the user tried to
      disable this module.

  <Returns>
    None
  """

  # Get the modulename
  dict_mark = input_dict
  try:
    command = dict_mark.keys()[0]
    while dict_mark[command]['name'] != 'modulename':
      dict_mark = input_dict[command]['children']
      command = dict_mark.keys()[0]
    modulename = command
  except IndexError:
    raise seash_exceptions.UserError("Error, command requires a modulename")

  if modulename == 'modules':
    raise seash_exceptions.UserError("Error, cannot disable the 'modules' module")

  seash_modules.disable(seash_dictionary.seashcommanddict, modulename)



def print_module_help(input_dict, environment_dict):
  """
  <Purpose>
    Displays the module level help for a module.

  <Arguments>
    input_dict:  The commanddict representing the user's input.
    environment_dict:  The dictionary representing the current seash 
                       environment.

  <Side Effects>
    The helptext for the module specified in the 'modulename' node will be 
    printed to stdout.

  <Exceptions>
    UserError:
      input_dict did not contain a 'modulename' node, or the user specified
      a module that is not installed.

  <Returns>
    None
  """

  # Get the modulename
  dict_mark = input_dict
  try:
    command = dict_mark.keys()[0]
    while dict_mark[command]['name'] != 'modulename':
      dict_mark = input_dict[command]['children']
      command = dict_mark.keys()[0]
    modulename = command
  except IndexError:
    raise seash_exceptions.UserError("Error, command requires a modulename")

  # Is this module installed?
  if not modulename in seash_modules.module_data:
    raise seash_exceptions.UserError("Module is not installed.")

  print seash_modules.module_data[modulename]['help_text']

  # Now, print out all the commands under this module
  print "Commands in this module:"
  print '\n'.join(seash_helper.get_commands_from_commanddict(seash_modules.module_data[modulename]['command_dict']))
  

