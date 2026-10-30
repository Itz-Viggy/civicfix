"""Offline official geometry and conservative, source-backed intake routing."""
import hashlib,json
from pathlib import Path
from shapely.geometry import shape,Point
from shapely import transform as coordinate_transform
from shapely.ops import unary_union
def transform(fn,geom): return coordinate_transform(geom,fn,interleaved=False)
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'routing'
META=json.loads((DATA/'sources.json').read_text())
for name,digest in [('gainesville.geojson',META['sha256']),('streets.geojson',META['streets']['sha256'])]:
    if hashlib.sha256((DATA/name).read_bytes()).hexdigest()!=digest: raise RuntimeError('Routing data checksum mismatch')
project=Transformer.from_crs(4326,26917,always_xy=True).transform
CITY=unary_union([shape(f['geometry']) for f in json.loads((DATA/'gainesville.geojson').read_text())['features']])
METRIC=transform(project,CITY)
STREETS=[(transform(project,shape(f['geometry'])),f['properties']) for f in json.loads((DATA/'streets.geojson').read_text())['features'] if f.get('geometry')]
VERSION=META['version']
CITY_GUIDE='https://www.gainesvillefl.gov/Government-Pages/Government/Departments/Strategy-Planning-Innovation/myGNV'
GRU_GUIDE='https://www.gru.com/My-Home/Customer-Service/Report-Streetlight-Outage'

def boundary(location):
    if not location: return 'outside'
    p=Point(location['longitude'],location['latitude']);q=transform(project,p)
    if q.distance(METRIC.boundary)<=max(10,location.get('accuracy') or 0): return 'boundary_uncertain'
    return 'inside' if CITY.contains(p) else 'outside'

def resolve(location,category):
    out={'status':'unresolved','route_id':None,'jurisdiction':None,'destination_name':None,'portal_url':None,'rules_version':VERSION,'boundary_version':VERSION,'source_urls':[CITY_GUIDE,META['boundary_source']],'verified_at':'2026-10-30','reason_codes':[]}
    if not location: out['reason_codes']=['missing_location'];return out
    if not location.get('confirmed'):out['reason_codes']=['unconfirmed_location'];return out
    b=boundary(location)
    if b!='inside':out['reason_codes']=['boundary_uncertain' if b=='boundary_uncertain' else 'outside_service_area'];return out
    if not category:out['reason_codes']=['missing_category'];return out
    if category=='leaking_hydrant':
        out.update(reason_codes=['no_verified_online_form'],source_urls=['https://www.gru.com/Home/Customer-Service'],guidance='Contact GRU for hydrant/water-leak guidance. No category-specific nonemergency web form verified.');return out
    if category=='broken_streetlight':
        out.update(reason_codes=['unknown_ownership'],source_urls=[GRU_GUIDE],guidance='GRU has a streetlight outage form, but pole ownership and outage versus structural damage must be established. Contact GRU for guidance.');return out
    if category in ['pothole','damaged_sign']:
        p=transform(project,Point(location['longitude'],location['latitude']))
        roads=[a for geom,a in STREETS if geom.distance(p)<=10]
        out['source_urls'].append(META['streets']['source'])
        if not roads or any(a.get('MAINTBY')!='City of Gainesville' for a in roads):out['reason_codes']=['unknown_ownership'];return out
    out.update(status='resolved',route_id='mygnv',jurisdiction='City of Gainesville',destination_name='myGNV — City nonemergency intake',portal_url='https://gainesvillefl.citysourced.com/servicerequests/create')
    return out
