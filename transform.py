
'''
Transform a GTFS (General Transit Feed Specification) file into an undirected
GEXF (Graph Exchange XML Format) graph.

The GTFS file must be unzipped into a directory called 'data' in the working
directory which this script is called from. Output is saved as out.gexf in
the current working directory.

Currently this script does not take command-line options, but you can modify
the constants defined at the top to configure the script to your liking.
'''

# GTFS defines these route types
LRT_TYPE = '0'
SUBWAY_TYPE = '1'
RAIL_TYPE = '2'
BUS_TYPE = '3'
FERRY_TYPE = '4'
CABLE_CAR_TYPE = '5'
GONDOLA_TYPE = '6'
FUNICULAR_TYPE = '7'

# Root of the extracted GTFS file
DATA_ROOT = 'mta/'

# You can filter the type of stop converted by placing the route types
# you're interested in in this list.
CONVERT_ROUTE_TYPES = [SUBWAY_TYPE]

# This defines an optional mapping on station names. Because stations
# are uniquely identified by their station name, this can be used to
# merge two nodes (stations) into one.
STATION_MAP = {
}

# Sometimes there are stations you may want to discard altogether
# (including their edges). They can be added to this set.
DISCARD_STATIONS = set([
])

# A function for normalizing a stop name. Can be used to eg. remove
# a platform name or direction.
def get_stop_name(stop_name):
    name = stop_name
    #name = stop_name.split(' - ')[0]
    return STATION_MAP.get(name, name)
 
def get_stop_id(stop_id):
    return stop_id[:-1]

from csv import DictReader
from itertools import groupby
from xml.dom.minidom import Document

class GEXF(object):
    def __init__(self):
        self.doc = Document()
        gexf = self.doc.createElement('gexf')
        gexf.setAttribute('xmlns', 'http://www.gexf.net/1.2draft')
        gexf.setAttribute('version', '1.2')
        gexf.setAttribute('xmlns:viz', 'http://www.gexf.net/1.2draft/viz')

        graph = self.doc.createElement('graph')
        graph.setAttribute('defaultedgetype', 'undirected')

        self.nodes = graph.appendChild(self.doc.createElement('nodes'))
        self.edges = graph.appendChild(self.doc.createElement('edges'))

        gexf.appendChild(graph)
        self.doc.appendChild(gexf)

    def add_node(self, node_id, label, x, y):
        node = self.doc.createElement('node')
        node.setAttribute('id', node_id)
        node.setAttribute('label', label)
        
        viz_position = self.doc.createElement('viz:position')
        viz_position.setAttribute('x', x)
        viz_position.setAttribute('y', y)

        node.appendChild(viz_position)
        self.nodes.appendChild(node)

    def add_edge(self, source, target, color):
        edge = self.doc.createElement('edge')
        edge.setAttribute('source', source)
        edge.setAttribute('target', target)

        if color == '':
            r, g, b = (0, 0, 0)
        else:
            r = int(color[:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:], 16)
        viz_color = self.doc.createElement('viz:color')
        viz_color.setAttribute('r', str(r))
        viz_color.setAttribute('g', str(g))
        viz_color.setAttribute('b', str(b))

        edge.appendChild(viz_color)
        self.edges.appendChild(edge)

    def write(self, fh):
        self.doc.writexml(fh, indent='\n', addindent='  ')

def main():
    trips_csv = DictReader(file(DATA_ROOT+'trips.txt'))
    stops_csv = DictReader(file(DATA_ROOT+'stops.txt'))
    stop_times_csv = DictReader(file(DATA_ROOT+'stop_times.txt'))
    routes_csv = DictReader(file(DATA_ROOT+'routes.txt'))

    gexf = GEXF()

    routes = dict()
    for route in routes_csv:
        if route['route_type'] in CONVERT_ROUTE_TYPES:
            routes[route['route_id']] = route
    print 'routes', len(routes)

    trips = dict()
    for trip in trips_csv:
        if trip['route_id'] in routes:
            trip['color'] = routes[trip['route_id']]['route_color']
            trips[trip['trip_id']] = trip
    print 'trips', len(trips)

    stops = set()
    edges = dict()
    for trip_id, stop_time_iter in groupby(stop_times_csv, lambda stop_time: stop_time['trip_id']):
        if trip_id in trips:
            trip = trips[trip_id]
            prev_stop = stop_time_iter.next()['stop_id']
            stops.add(prev_stop)
            for stop_time in stop_time_iter:
                stop = stop_time['stop_id']
                edge = (prev_stop, stop)
                edges[edge] = trip['color']
                stops.add(stop)
                prev_stop = stop
    print 'stops', len(stops)
    print 'edges', len(edges)

    #stop_map = dict()
    stops_used = set(DISCARD_STATIONS)
    for stop in stops_csv:
        if stop['stop_id'] in stops:
            stop_id = get_stop_id(stop['stop_id'])
            #name = get_stop_name(stop['stop_name'])
            #stop_map[stop['stop_id']] = name
            name = stop['stop_name']
            #if name not in stops_used:
            if stop_id not in stops_used:
                gexf.add_node(stop_id, name, stop['stop_lon'], stop['stop_lat'])
                stops_used.add(stop_id)
    #print 'stop_map', len(stop_map)

    edges_used = set()
    for (start_stop_id, end_stop_id), color in edges.iteritems():
        #start_stop_name = stop_map[start_stop_id]
        #end_stop_name = stop_map[end_stop_id]
        start_stop_id = get_stop_id(start_stop_id)
        end_stop_id = get_stop_id(end_stop_id)
        #if start_stop_name in DISCARD_STATIONS or end_stop_name in DISCARD_STATIONS:
        #    continue
        edge = min((start_stop_id, end_stop_id), (end_stop_id, start_stop_id))
        if edge not in edges_used:
            gexf.add_edge(start_stop_id, end_stop_id, color)
            edges_used.add(edge)

    gexf.write(file('out.gexf', 'w'))

if __name__ == '__main__':
    main()

