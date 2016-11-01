"""
<Author>
  Evan Meagher

<Start Date>
  January 15, 2010

<Description>
  This script runs an all-pairs ping on a set of allocated nodes and generates
  a Google Maps mashup displaying node locations and latencies.

  Built on run_program.py example script provided by Justin Samuel

  Command-line switches:
    --output
      Specify where to write/display output. If given 'localhost', appmap.py
      will host output webpage on localhost. If any other value is given,
      output will be written to a local file whose name is the value itself.
      If --output flag not given, appmap.py will default is using localhost.
      
    --num-nodes
      Specify the number of nodes to acquire and use for all-pairs ping. If
      left out, any vessels previously acquired using Seattle GENI will be
      used. Note that all nodes are released after script runs.

    --local-port
      Specify the localhost port on which to host the output webpage. Default
      port 1070 will be used if --local-port switch left out. If --ouput
      command-line switch set to write to a local file, --local-port will be
      ignored.
      
    --insecure
      Run appmap.py without using a secure SSL connection to SeattleGENI. If
      `--insecure` is not set, M2Crypto must be installed and the current
      directory must contain a valid PEM file containing CA certificates that
      you trust.


  NOTE: By default, appmap.py makes a secure connection to SeattleGENI.
  To perform secure SSL communication with SeattleGENI, you must:
    * Have M2Crypto installed (http://chandlerproject.org/Projects/MeTooCrypto)
    * Have a PEM file, cacert.pem, containing CA certificates in the same
      directory as appmap.py One such file can be found at
      http://curl.haxx.se/ca/cacert.pem

  More info at https://seattle.cs.washington.edu/wiki/SeattleGeniClientLib

<Usage>
  python appmap.py GENI_USERNAME [--output=localhost|FILENAME] [--num-nodes=
  NUM_NODES_TO_ACQUIRE] [--local-port=PORT] [--insecure]
"""

import os
import sys
import repyportability
import experimentlib
import repyhelper
repyhelper.translate_and_import("serialize.repy")
repyhelper.translate_and_import("listops.repy")
repyhelper.translate_and_import("geoip_client.repy")
repyhelper.translate_and_import("httpretrieve.repy")
repyhelper.translate_and_import("httpserver.repy")

# If this script resides outside of the directory that contains the seattlelib
# files and experimentlib.py, then you'll need to set that path here. If you
# downloaded an installer (even if you haven't installed seattle on the machine
# this script resides on), the path will be to the seattle_repy directory from
# the extracted installer. 
#PATH_TO_SEATTLE_REPY = "/path/to/seattle_repy"
#sys.path.append(PATH_TO_SEATTLE_REPY)


# Dict to store variables needed by display_results() callback function
CBFUNC_CONTEXT = {}

NODEIPLIST = []
SERVABLE_FILES = ['style.css', 'jquerygmaps.js', 'map_marker_icon.png', 'map_marker_sel_icon.png']



def recv_all(connobj):
  """
  <Purpose>
    Wrapper function for receiving all sent bytes from TCP connection.

  <Arguments>
    connobj:
      socket-like object

  <Exceptions>
    Exception if the socket is closed either locally or remotely.

  <Side Effects>
    None.
    
  <Returns>
    The data received from the socket, in its entirety.
  """
  
  retstr = recvd = connobj.recv(16777216)
  while recvd != "":
    try:
      recvd = connobj.recv(16777216)
      retstr += recvd
    except Exception, e:
      # Ignore exceptions and exit the loop
      break
  return retstr



def generate_node_list():
  """
  <Purpose>
    Generates an HTMl string of an unsorted list of nodes.
  
  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    None.
    
  <Returns>
    HTML string of unsorted list of nodes.
  """

  nodelist_str = '<ul id="coords">'
  for nodeip in sorted(NODEIPLIST):
    # Get node location information
    location_dict = geoip_record_by_addr(nodeip)

    # Print node list element
    nodelist_str = nodelist_str + '<li id="node' + str(sorted(NODEIPLIST).index(nodeip)) + '"><span class="nodeip">' + str(nodeip) + '</span><span class="longitude">' + str(location_dict['longitude']) + '</span><span class="latitude">' + str(location_dict['latitude']) + '</span><span class="locationname">' + geoip_location_str(location_dict) + '</span></li>'
    
  nodelist_str = nodelist_str + '</ul>'
  
  return nodelist_str


  
def generate_adj_matrix(latdict):
  """
  <Purpose>
    Generates an HTMl string of a table containing node latency information.
    Maps mashup.
  
  <Arguments>
    latdict:
      Dictionary containing all-pairs ping latencies between nodes.

  <Exceptions>
    None.

  <Side Effects>
    None.
    
  <Returns>
    HTML string of node adjacency table.
  """

  adj_matrix_str = '<table id="latency_matrix"><tr><th></th>'

  # Table column headers
  for ip in sorted(NODEIPLIST):
    adj_matrix_str = adj_matrix_str + '<th>' + str(ip) + '</th>'
  adj_matrix_str = adj_matrix_str + '</tr>'

  # Iterate through NODEIPLIST, writing latency information, if present.
  # Note: the string 'source_id + "_" + target_id' in the td elements'
  # class names is used by jQuery to get node latencies.
  source_id = 0
  for ip in sorted(NODEIPLIST):
    adj_matrix_str = adj_matrix_str + '<tr><th>' + str(ip) + '</th>'
    target_id = 0
    if ip in latdict:
      for adjip in sorted(NODEIPLIST):
        adj_matrix_str = adj_matrix_str + '<td class="' + str(source_id) + '_' + str(target_id) + '">'
        if adjip in latdict[ip]:
          adj_matrix_str = adj_matrix_str + str(latdict[ip][adjip]) + '</td>'
        else:
          adj_matrix_str = adj_matrix_str + 'N/A</td>'
        target_id += 1
      adj_matrix_str = adj_matrix_str + '</tr>'
      source_id += 1
    
  adj_matrix_str = adj_matrix_str + '</table>'

  return adj_matrix_str



def generate_html(latdict):
  """
  <Purpose>
    Generates an HTMl string of a webpage displaying node locations and
    latencies on a Google Maps mashup.
  
  <Arguments>
    latdict:
      Dictionary containing all-pairs ping latencies between nodes.

  <Exceptions>
    None.

  <Side Effects>
    None.
    
  <Returns>
    HTML string of output webpage.
  """

  # Doctype declaration, head element, and list of node locations and latencies
  retstr = \
  """
<!DOCTYPE html><html><head><title>Seattle Demo</title>
<script type="text/javascript" src="http://www.google.com/jsapi?key=ABQIAAAAvTO5bNvqH85lpidZNqtGBhRqO5-PGhVcLFlvVUbFkY6AHMZumBS3pxywBF64KR6Bi9PSnZpyVH9dPw"></script>
<script type="text/javascript">google.load("maps", "2.x"); google.load("jquery", "1.3.2");</script>
<script type="text/javascript" src="jquerygmaps.js"></script>
<link rel="stylesheet" type="text/css" href="style.css" /></head>
<body>
"""

  # Unordered list of nodes (to be parsed by jQuery), node tooltip div, map
  # div, and button to end demo
  retstr = retstr + generate_node_list() + \
  """
<div id='message' style='display: none;'></div>
<div id="map"></div>
<a href="?action=finish">Finish demo</a>
<h2>Node latency information</h2>
"""

  # Adjacency matrix and body and html closing tags
  retstr = retstr + generate_adj_matrix(latdict) + '</body>\n</html>\n'

  return retstr

  

def get_latencies():
  """
  <Purpose>
    Retrieves latency information (for all nodes) from a single node in
    NODEIPLIST.

  <Arguments>
    None.

  <Exceptions>
    Exception if the socket is closed either locally or remotely.
    ValueError if the string received from node is corrupted.
    TypeError if the type of 'data' used in string received from node isn't
    allowed.

  <Side Effects>
    None.
    
  <Returns>
    Dictionary of node latency information.
  """

  sampleip = NODEIPLIST[0]
  try:
    sock = repyportability.openconn(sampleip, CBFUNC_CONTEXT['geniport'])
    latency_dict = serialize_deserializedata(recv_all(sock))
  except Exception, e:
    raise
  finally:
    sock.close()
      
  return latency_dict



def display_results(reqdict):
  """
  <Purpose>
    Callback function for httpserver_registercallback. Handles requests for
    root webpage, style.css, jquerygmaps.js, and the two map icon .png files
    used in the output webpage.

  <Arguments>
    reqdict:
      A dictionary describing the HTTP request, as per the documentation of
      httpserver.repy.

  <Exceptions>
    Any exceptions thrown by get_latencies() or generate_html().
    IOError if open() or read() fail.

  <Side Effects>
    If output file specified, writes return value of generate_html() to a local
    HTML file. If localhost output specified, hosts return value of
    generate_html() on localhost:1070.
    
  <Returns>
    A dictionary containing request response information, as per the
    documentation of httpserver.repy.
  """
  
  msg = ""
  content_type = ""

  # Handle a request to finish demo
  if reqdict['querydict'] and reqdict['querydict']['action'] \
        and reqdict['querydict']['action'] == 'finish':
    httpserver_stopcallback(CBFUNC_CONTEXT['listenerid'])
    
    # Now that we're done with node-interaction, release them
    experimentlib.seattlegeni_release_vessels(CBFUNC_CONTEXT['identity'], CBFUNC_CONTEXT['vesselhandle_list'])
    print "Vessels released."
    msg = "<html><head><title>Seattle Demo</title></head><body>Demo finished</body></html>"
    content_type = "text/html"

  # Handle a request to view demo
  elif reqdict['path'] == '/':
    # If NODEIPLIST is empty, then die gracefully
    if not NODEIPLIST:
      print "Error: All acquired nodes failed. Please retry."
      sys.exit()
      
    try:
      latency_dict = get_latencies()
      msg = generate_html(latency_dict)
      content_type = "text/html"
    except Exception, e:
      if repr(e).startswith("timeout("):
        raise HttpConnectionError("Socket timed out connecting to host/port.")
      raise

  # Handle a request of file in SERVABLE_FILES
  elif reqdict['path'][1:] in SERVABLE_FILES:
    try:
      script_fo = open(reqdict['path'][1:], 'r')
      msg = script_fo.read()
    except IOError:
      raise
    finally:
      script_fo.close()
      
    if reqdict['path'][-4:] == '.css':
      content_type = 'text/css'
    elif reqdict['path'][-3:] == '.js':
      content_type = 'text/javascript'
    elif reqdict['path'][-4:] == '.png':
      content_type = 'image/png'
    
  # Request failed
  else:
    msg = "<html><head><title></title></head><body>Requested data not found</body></html>"
    retdict = {
      'version': '1.1',
      'statuscode': 404,
      'statusmsg': "Not found",
      'headers': { 'Content-Type': content_type,
                   'Content-Length': str(len(msg)),
                   'Connection': 'close'
                   },
      'message': msg
      }
    return retdict

  # If request succeeded, return requested data
  retdict = {
    'version': '1.1',
    'statuscode': 200,
    'statusmsg': "OK",
    'headers': { 'Content-Type': content_type,
                 'Content-Length': str(len(msg)),
                 'Connection': 'close'
                 },
    'message': msg
    }
  return retdict



def init():
  """
  <Purpose>
    Parses command-line arguments and generate configuartion dictionary on
    program start.

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    None.
    
  <Returns>
    Dictionary of configuration variables used in the rest of the script.
  """

  appmap_config = {
    'geni_username': "",
    'output': 'localhost',
    'num_nodes': 0,
    'local_port': 1070,
    'allow_ssl_insecure': None
    }
  
  # Provide usage information if insufficient arguments or 'help' flag is given
  if len(sys.argv) < 2 or sys.argv[1] == 'help':
    print """Usage: python appmap.py GENI_USERNAME [--output=localhost|FILENAME] [--num-nodes=NUM_NODES_TO_ACQUIRE] [--local-port=PORT] [--insecure]"

This script runs an all-pairs ping on a set of allocated nodes and generates
a Google Maps mashup displaying node locations and latencies.

Command-line switches:
  --output
    Specify where to write/display output. If given 'localhost', appmap.py
    will host output webpage on localhost. If any other value is given,
    output will be written to a local file whose name is the value itself.
    If --output flag not given, appmap.py will default is using localhost.
    
  --num-nodes
    Specify the number of nodes to acquire and use for all-pairs ping. If
    left out, any vessels previously acquired using Seattle GENI will be
    used. Note that all nodes are released after script runs.

  --local-port
    Specify the localhost port on which to host the output webpage. Default
    port 1070 will be used if --local-port switch left out. If --ouput
    command-line switch set to write to a local file, --local-port will be
    ignored.

  --insecure
    Run appmap.py without using a secure SSL connection to SeattleGENI. If
    `--insecure` is not set, M2Crypto must be installed and the current
    directory must contain a valid PEM file containing CA certificates that
    you trust.

NOTE: By default, appmap.py makes a secure connection to SeattleGENI.
      Check documentation for more details."""
    sys.exit()
    
  appmap_config['geni_username'] = sys.argv[1]
  for arg in sys.argv:
    if arg[:8] == '--output':
      appmap_config['output'] = arg.split("=")[-1]
    elif arg[:11] == '--num-nodes':
      appmap_config['num_nodes'] = arg.split("=")[-1]
    elif arg[:12] == '--local-port':
      appmap_config['local_port'] = int(arg.split("=")[-1])
      # Make sure a valid port was given
      if appmap_config['local_port'] < 1024 or appmap_config['local_port'] > 65535:
        print "Error: local port on which to host results must between 1000 and 5000"
        sys.exit()
    elif arg == '--insecure':
      appmap_config['allow_ssl_insecure'] = True

  return appmap_config
      


def main(appmap_config):
  # Set SSL security level and warn user if running without SSL
  experimentlib.SEATTLECLEARINGHOUSE_ALLOW_SSL_INSECURE = appmap_config['allow_ssl_insecure']
  if appmap_config['allow_ssl_insecure']:
    print "Running without secure SSL connection to SeattleGENI"
  
  # Get GENI user identity object and port
  CBFUNC_CONTEXT['identity'] = experimentlib.create_identity_from_key_files(appmap_config['geni_username'] + ".publickey", appmap_config['geni_username'] + ".privatekey")

  # If --insecure switch not used, attempt a secure SSL connection to
  # SeattleGENI. If SeattleClearinghouseError exception thrown, print warning.
  try:
    CBFUNC_CONTEXT['geniport'] = experimentlib.seattlegeni_user_port(CBFUNC_CONTEXT['identity'])
  except Exception, e:
    if repr(e).startswith("SeattleClearinghouseError"):
      print """Error: Cannot make secure SSL connection to SeattleGENI
Please make sure that:
  * M2Crypto is installed
  * the current directory contains a valid PEM file containing CA certificates

To run appmap.py without SSL authentication, use the `--insecure` switch. Check documentation for more details."""

      sys.exit()
    
  # Get list of vessels user has previously allocated
  CBFUNC_CONTEXT['vesselhandle_list'] = experimentlib.seattlegeni_get_acquired_vessels(CBFUNC_CONTEXT['identity'])

  if appmap_config['num_nodes'] > 0 and len(CBFUNC_CONTEXT['vesselhandle_list']) > 0:
    # Release any vessels previously acquired from GENI
    experimentlib.seattlegeni_release_vessels(CBFUNC_CONTEXT['identity'], CBFUNC_CONTEXT['vesselhandle_list'])

  if appmap_config['num_nodes'] > 0:
    # Acquire argument number of vessels using seattlegeni interface
    CBFUNC_CONTEXT['vesselhandle_list'] = experimentlib.seattlegeni_acquire_vessels(CBFUNC_CONTEXT['identity'], "wan", int(appmap_config['num_nodes']))

  # If no vessels were acquired, an error occurred and script exits
  if len(CBFUNC_CONTEXT['vesselhandle_list']) == 0:
    print "Error: No vessels acquired. Try rerunning " + sys.argv[0]
    sys.exit()
    
  nodelocation_list = []
  vessel_details = experimentlib.seattlegeni_get_acquired_vessels_details(CBFUNC_CONTEXT['identity'])
  for vessel in vessel_details:
    nodelocation_list.append(vessel["nodelocation"])

  print("Number of vessels acquired: " + str(len(CBFUNC_CONTEXT['vesselhandle_list'])))
  
  # Write node IPs to file to be uploaded
  neighborip_fo = open("neighboriplist.txt", "w")
  for ipport in nodelocation_list:
    ip = ipport.split(":")[0]
    NODEIPLIST.append(ip)
    neighborip_fo.write(ip + "\n")
  neighborip_fo.close()

  
  # Using experimentlib.run_parallelized() to upload and run programs
  uploadips_success, uploadips_fail = experimentlib.run_parallelized(CBFUNC_CONTEXT['vesselhandle_list'], experimentlib.upload_file_to_vessel, CBFUNC_CONTEXT['identity'], "neighboriplist.txt")
  uploadprog_success, uploadprog_fail = experimentlib.run_parallelized(CBFUNC_CONTEXT['vesselhandle_list'], experimentlib.upload_file_to_vessel, CBFUNC_CONTEXT['identity'], "pingneighbors.py")
  start_success, start_fail = experimentlib.run_parallelized(CBFUNC_CONTEXT['vesselhandle_list'], experimentlib.start_vessel, CBFUNC_CONTEXT['identity'], "pingneighbors.py", [str(CBFUNC_CONTEXT['geniport'])])

  # Handle failed nodes
  for failed in listops_uniq(uploadips_fail + uploadprog_fail + start_fail):
    nodeid, vesselname = experimentlib.get_nodeid_and_vesselname(failed[0])
    for vessel in vessel_details:
      if vessel["nodeid"] == nodeid:
        NODEIPLIST.remove(vessel["nodelocation"][:-5])
    print "Failure on vessel " + failed[0] + ". Error was: " + failed[1]
  print "Files uploaded to nodes and programs running"


  # Now that vessel setup is complete, handle output
  geoip_init_client("http://geoip.cs.washington.edu:12679")
  if appmap_config['output'] == 'localhost':
    # Set up http listener to display results
    CBFUNC_CONTEXT['listenerid'] = httpserver_registercallback(("localhost", appmap_config['local_port']), display_results)
    print "Browse to 'http://localhost:" + str(appmap_config['local_port']) + "' to view results."
  else:
    print "Sleeping for 25 seconds to let latencies percolate across vessels."
    sleep(25)
    latency_dict = get_latencies()
    htmlstr = generate_html(latency_dict)
    output_fo = open(appmap_config['output'], 'w')
    output_fo.write(htmlstr)
    output_fo.close()

    # Release vessels
    experimentlib.seattlegeni_release_vessels(CBFUNC_CONTEXT['identity'], CBFUNC_CONTEXT['vesselhandle_list'])
    
    print "Done."
    print "Browse to '" + os.getcwd() + "/" + appmap_config['output'] + "' to view results."



    
if __name__ == "__main__":
  appmap_config = init()
  main(appmap_config)
