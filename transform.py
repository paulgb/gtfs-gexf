
from csv import DictReader
from itertools import groupby
from xml.dom.minidom import Document

LRT_TYPE = '0'
SUBWAY_TYPE = '1'
RAIL_TYPE = '2'
BUS_TYPE = '3'
FERRY_TYPE = '4'
CABLE_CAR_TYPE = '5'
GONDOLA_TYPE = '6'
FUNICULAR_TYPE = '7'

class GEXF(object):
    def __init__(self):
        self.doc = Document()
        gexf = self.doc.createElement('gexf')
        gexf.setAttribute('xmlns', 'http://www.gexf.net/1.2draft')
        gexf.setAttribute('version', '1.2')
        gexf.setAttribute('xmlns:viz', 'http://www.gexf.net/1.2draft/viz')

        graph = self.doc.createElement('graph')

        self.nodes = graph.appendChild(self.doc.createElement('nodes'))
        self.edges = graph.appendChild(self.doc.createElement('edges'))

        gexf.appendChild(graph)
        self.doc.appendChild(gexf)

    def add_node(self, node_id, x, y):
        node = self.doc.createElement('node')
        node.setAttribute('id', node_id)
        node.setAttribute('label', node_id)
        
        viz_position = self.doc.createElement('viz:position')
        viz_position.setAttribute('x', x)
        viz_position.setAttribute('y', y)

        node.appendChild(viz_position)
        self.nodes.appendChild(node)

    def add_edge(self, source, target):
        edge = self.doc.createElement('edge')
        edge.setAttribute('source', source)
        edge.setAttribute('target', target)

        self.edges.appendChild(edge)

    def write(self, fh):
        self.doc.writexml(fh)

def main():
    trips_csv = DictReader(file('data/trips.txt'))
    stops_csv = DictReader(file('data/stops.txt'))
    stop_times_csv = DictReader(file('data/stop_times.txt'))
    routes_csv = DictReader(file('data/routes.txt'))

    gexf = GEXF()

    routes = dict()
    for route in routes_csv:
        if route['route_type'] == SUBWAY_TYPE:
            routes[route['route_id']] = route
    print 'routes', len(routes)

    trips = dict()
    for trip in trips_csv:
        if trip['route_id'] in routes:
            trips[trip['trip_id']] = trip
    print 'trips', len(trips)

    stops = set()
    edges = set()
    for trip_id, stop_time_iter in groupby(stop_times_csv, lambda stop_time: stop_time['trip_id']):
        if trip_id in trips:
            prev_stop = stop_time_iter.next()['stop_id']
            stops.add(prev_stop)
            for stop_time in stop_time_iter:
                stop = stop_time['stop_id']
                edges.add((prev_stop, stop))
                stops.add(stop)
                prev_stop = stop
    print 'stops', len(stops)
    print 'edges', len(edges)

    stop_map = dict()
    for stop in stops_csv:
        if stop['stop_id'] in stops:
            name = stop['stop_name'].split(' - ')[0]
            stop_map[stop['stop_id']] = name
            gexf.add_node(name, stop['stop_lon'], stop['stop_lat'])
    print 'stop_map', len(stop_map)

    for (start_stop_id, end_stop_id) in edges:
        start_stop_name = stop_map[start_stop_id]
        end_stop_name = stop_map[end_stop_id]
        gexf.add_edge(start_stop_name, end_stop_name)

    gexf.write(file('out.gexf', 'w'), addindent='  ')

if __name__ == '__main__':
    main()

