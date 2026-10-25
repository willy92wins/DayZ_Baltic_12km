"""OSM shared-node connectivity inside the crop; not a vehicle routing test."""
from collections import Counter
import argparse,json, math
import osmium
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from geo_common import *

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--narva-detail',action='store_true')
    args=parser.parse_args()
    features=json.loads((DERIVED/'gis/osm_roads_wgs84.geojson').read_text(encoding='utf-8'))['features']
    selected={int(f['properties']['osm_id'].split('/')[1]):f['properties'] for f in features}
    if args.narva_detail:
        detail=json.loads((DERIVED/'gis/narva_crossing_detail_wgs84.geojson').read_text(encoding='utf-8'))['features']
        selected.update({int(f['properties']['osm_id'].split('/')[1]):f['properties'] for f in detail})
    nodes={}; edges={}; edge_ways={}; seen=set(); conflicts=set(); restricted=0
    for source in json.loads((EVIDENCE/'source-manifest.json').read_text())['sources']:
        if source['group']!='osm':continue
        ids={i for i,p in selected.items() if p['source_extract']==source['filename']}
        stream=osmium.FileProcessor(source['path']).with_locations().with_filter(osmium.filter.EntityFilter(osmium.osm.WAY)).with_filter(osmium.filter.IdFilter(ids))
        for way in stream:
            assert way.version==selected[way.id]['osm_version']
            seen.add(way.id); previous=None
            if way.tags.get('access') in {'no','private'}:restricted+=1
            for n in way.nodes:
                assert n.location.valid()
                if not (WEST<=n.lon<=EAST and SOUTH<=n.lat<=NORTH):
                    previous=None;continue
                x,y=game_xy(n.lon,n.lat);xy=(float(x),float(y))
                if n.ref in nodes and math.dist(nodes[n.ref],xy)>.05:conflicts.add(n.ref)
                nodes.setdefault(n.ref,xy)
                if previous is not None and previous!=n.ref:
                    key=tuple(sorted((previous,n.ref)))
                    edges.setdefault(key,math.dist(nodes[previous],nodes[n.ref]))
                    edge_ways.setdefault(key,way.id)
                previous=n.ref
        print('ROAD NODES '+source['filename']+' '+str(len(nodes)),flush=True)
    assert seen==set(selected),'A selected way is missing from its pinned source'
    ids=list(nodes);index={v:i for i,v in enumerate(ids)};xy=np.asarray([nodes[v] for v in ids])
    rows=[];cols=[];weights=[]
    for (a,b),weight in edges.items():
        if weight<=0:continue
        rows.extend([index[a],index[b]]);cols.extend([index[b],index[a]]);weights.extend([weight,weight])
    graph=coo_matrix((weights,(rows,cols)),shape=(len(ids),len(ids))).tocsr()
    ncomp,labels=connected_components(graph,directed=False)
    tree=cKDTree(xy);anchors=[]
    points=json.loads((EVIDENCE/'georef-v0.json').read_text())['points']
    for point in points:
        position=game_xy(point['lon'],point['lat'])
        distance,i=tree.query(position);anchors.append({'name':point['name'],'node_id':ids[i],'node_index':int(i),'snap_distance_game_m':float(distance),'component':int(labels[i])})
    paths=[]
    distances,predecessors=dijkstra(graph,directed=False,indices=[a['node_index'] for a in anchors],return_predecessors=True)
    for i,a in enumerate(anchors):
        for b in anchors[i+1:]:
            length=float(distances[i,b['node_index']])
            paths.append({'from':a['name'],'to':b['name'],'connected':math.isfinite(length),'length_game_m':length if math.isfinite(length) else None})
    counts=Counter(labels.tolist())
    crossing_route=[]
    start=next(i for i,a in enumerate(anchors) if a['name']=='Narva')
    target=next(a['node_index'] for a in anchors if a['name']=='San Petersburgo')
    if math.isfinite(distances[start,target]):
        current=target;way_ids=set()
        while current!=anchors[start]['node_index']:
            previous=int(predecessors[start,current]);assert previous>=0
            way_ids.add(edge_ways[tuple(sorted((ids[previous],ids[current])))])
            current=previous
        crossing_route=[dict(selected[i]) for i in sorted(way_ids) if selected[i]['highway'] not in {'motorway','trunk','primary','secondary','tertiary','motorway_link','trunk_link','primary_link','secondary_link','tertiary_link'}]
    save_json(EVIDENCE/('road-topology-with-narva-detail.json' if args.narva_detail else 'road-topology.json'),{
      'status':'ANALYSIS_ONLY','method':'Undirected graph of shared OSM node IDs; full internal consecutive segments only; no outside-crop detours. Same selected way/version/source as the exported layer.',
      'nodes':len(nodes),'edges':len(edges),'components':ncomp,'largest_component_nodes':counts.most_common(1)[0][1],
      'cross_extract_node_coordinate_conflicts_over_005_game_m':len(conflicts),
      'restricted_access_ways_included':restricted,
      'bridge_tagged_ways':sum(f['properties'].get('bridge') not in {None,'no'} for f in features),
      'tunnel_tagged_ways':sum(f['properties'].get('tunnel') not in {None,'no'} for f in features),
      'anchors':anchors,'anchor_paths':paths,
      'narva_saint_petersburg_non_major_ways_on_shortest_undirected_path':crossing_route,
      'limitations':['Not a drivable network: ignores one-way rules, turn restrictions and permissions; private/no-access ways remain visible reference geometry.',
      'Residential/service/local streets omitted from selected road classes; disconnected components do not establish broken source geography.',
      'Bridge/tunnel counts are OSM ways, not unique structures; all require human-scale assets and clearance checks.',
      'Terrain slopes, water depths, vanilla bridge fit and gameplay choke points are not validated by this graph.']})
    print('TOPOLOGY '+str(ncomp)+' components; anchors connected '+str(all(p['connected'] for p in paths)),flush=True)

if __name__=='__main__':main()
