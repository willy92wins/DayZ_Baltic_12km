"""Select connected main routes from pinned OSM node topology, preserving provenance.

Undirected gameplay layout only; no road pieces, legal routing or grading claim.
"""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
import osmium
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from geo_common import WEST,EAST,SOUTH,NORTH,game_xy,save_json
OUT=ROOT/'evidence/regional-foundation-v1'


def main():
    source_paths=[ROOT/'derived/gis/osm_roads_wgs84.geojson',ROOT/'derived/gis/narva_crossing_detail_wgs84.geojson']
    selected={int(f['properties']['osm_id'].split('/')[1]):f['properties']
              for p in source_paths for f in json.loads(p.read_text(encoding='utf-8'))['features']}
    nodes,edges,edge_ways={}, {}, {}
    seen=set()
    for source in json.loads((ROOT/'evidence/source-manifest.json').read_text())['sources']:
        if source['group']!='osm':continue
        ids={i for i,p in selected.items() if p['source_extract']==source['filename']}
        stream=osmium.FileProcessor(source['path']).with_locations().with_filter(osmium.filter.EntityFilter(osmium.osm.WAY)).with_filter(osmium.filter.IdFilter(ids))
        for way in stream:
            assert way.version==selected[way.id]['osm_version']
            seen.add(way.id)
            previous=None
            for node in way.nodes:
                assert node.location.valid()
                if not(WEST<=node.lon<=EAST and SOUTH<=node.lat<=NORTH):
                    previous=None
                    continue
                x,z=game_xy(node.lon,node.lat)
                pos=(float(x),float(z))
                if node.ref in nodes and math.dist(nodes[node.ref],pos)>.05:
                    raise ValueError('Conflicting pinned OSM node coordinates')
                nodes.setdefault(node.ref,pos)
                if previous is not None and previous!=node.ref:
                    key=tuple(sorted((previous,node.ref)))
                    edges.setdefault(key,math.dist(nodes[previous],pos))
                    edge_ways.setdefault(key,way.id)
                previous=node.ref
        print(f'Pinned graph read: {source["filename"]}, {len(nodes)} nodes',flush=True)
    assert seen==set(selected),'Missing selected way'
    node_ids=list(nodes)
    index={v:i for i,v in enumerate(node_ids)}
    xy=np.asarray([nodes[v] for v in node_ids])
    rows,cols,weights=[],[],[]
    for (a,b),length in edges.items():
        if length<=0:continue
        rows.extend([index[a],index[b]])
        cols.extend([index[b],index[a]])
        weights.extend([length,length])
    graph=coo_matrix((weights,(rows,cols)),shape=(len(xy),len(xy))).tocsr()
    ncomp,labels=connected_components(graph,directed=False)
    tree=cKDTree(xy)
    points=json.loads((ROOT/'evidence/georef-v0.json').read_text())['points']
    aliases={'Kotlin/Kronstadt':{'кронштадт','kronstadt'},'Shlisselburg':{'шлиссельбург','shlisselburg'},
             'Veliky Novgorod':{'великий новгород','veliky novgorod'}}
    places=json.loads((ROOT/'derived/gis/osm_places_wgs84.geojson').read_text(encoding='utf-8'))['features']
    for name,names in aliases.items():
        matches=[f for f in places if f['geometry']['type']=='Point' and
                 any(str(v).casefold() in names for k,v in f['properties'].items() if k.startswith('name'))]
        if len(matches)!=1:raise ValueError(f'Expected one pinned place for {name}: {len(matches)}')
        f=matches[0]
        points.append({'name':name,'lon':f['geometry']['coordinates'][0],'lat':f['geometry']['coordinates'][1],'osm_id':f['properties']['osm_id']})
    anchors=[]
    for p in points:
        d,i=tree.query(game_xy(p['lon'],p['lat']))
        anchors.append({'name':p['name'],'node_id':node_ids[i],'index':int(i),'snap_m':float(d),'component':int(labels[i]),'xz':xy[i].tolist()})
    assert len({a['component'] for a in anchors})==1,'An anchor has no connection'
    distances,previous=dijkstra(graph,directed=False,indices=[a['index'] for a in anchors],return_predecessors=True)
    route_edges=set()
    routes=[]
    for ai,a in enumerate(anchors):
        for b in anchors[ai+1:]:
            current=b['index']
            ordered=[node_ids[current]]
            while current!=a['index']:
                prev=int(previous[ai,current])
                if prev<0:raise ValueError('Unreachable anchor')
                key=tuple(sorted((node_ids[prev],node_ids[current])))
                route_edges.add(key)
                ordered.append(node_ids[prev])
                current=prev
            routes.append({'from':a['name'],'to':b['name'],'length_m':float(distances[ai,b['index']]),'node_ids':ordered[::-1]})
    degrees=Counter(n for edge in route_edges for n in edge)
    selected_nodes=sorted(degrees)
    features=[]
    for a,b in sorted(route_edges):
        way=edge_ways[(a,b)]
        props=dict(selected[way],node_a=a,node_b=b,length_m=edges[(a,b)])
        features.append({'type':'Feature','properties':props,'geometry':{'type':'LineString','coordinates':[nodes[a],nodes[b]]}})
    save_json(OUT/'road-network-game.json',{'type':'FeatureCollection','coordinate_system':'local game X/Z metres','features':features})
    save_json(OUT/'road-network-routes.json',{'anchors':anchors,'routes':routes,'nodes':{str(n):nodes[n] for n in selected_nodes}})
    report={'status':'SELECTED_NOT_GRADED','method':'Union of shortest undirected routes for every pair of 11 pinned geographic anchors; shared OSM node IDs only.',
            'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
            'source_graph_nodes':len(nodes),'source_graph_edges':len(edges),'source_components':ncomp,
            'anchors':anchors,'routes':len(routes),'selected_edges':len(route_edges),'selected_nodes':len(selected_nodes),
            'length_m':sum(edges[e] for e in route_edges),'junctions_degree_ge_3':sum(v>=3 for v in degrees.values()),
            'way_classes':dict(Counter(f['properties']['highway'] for f in features)),
            'limitations':['Main layout selection; one-way rules, access restrictions and lane count are not preserved.',
                           'No physical road pieces or driving acceptance. Crossings require separate water/bridge engineering.',
                           'Remaining OSM roads retained as reference, not erased.']}
    save_json(OUT/'road-network-selection.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in {'anchors','source_sha256'}},indent=2))


if __name__=='__main__':main()
