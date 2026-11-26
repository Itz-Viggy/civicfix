"""Offline destination lookup using Gainesville's official boundary and street inventory."""
import hashlib
import json
import logging
from functools import cache
from pathlib import Path

from pyproj import Transformer
from pyproj.exceptions import ProjError
from shapely import STRtree, transform as coordinate_transform
from shapely.errors import ShapelyError
from shapely.geometry import Point, shape
from shapely.ops import unary_union

DATA = Path(__file__).resolve().parents[3] / 'routing'
META = json.loads((DATA / 'sources.json').read_text())
BOUNDARY_VERSION = META['version']
RULES_VERSION = META['rules_version']
GRU_GUIDE = 'https://www.gru.com/My-Home/Customer-Service/Report-Streetlight-Outage'
CITY_MAINTAINER = 'City of Gainesville'
ROAD_MATCH_METRES = 10
NEARBY_ROAD_METRES = 50
ROAD_LOCATION_GUIDANCE = 'Place the pin on the affected roadway and enter its street name and nearest cross street.'
LOOKUP_FAILED_GUIDANCE = 'CivicFix could not check its local routing data. Try checking the destination again.'
logger = logging.getLogger(__name__)
project = Transformer.from_crs(4326, 26917, always_xy=True).transform


class RoutingDataError(Exception):
    pass


LOOKUP_ERRORS = (RoutingDataError, ShapelyError, ProjError)


def transform(fn, geom):
    return coordinate_transform(geom, fn, interleaved=False)


def features(name, sha256):
    try:
        data = (DATA / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != sha256:
            raise RoutingDataError(f'{name} checksum mismatch')
        result = [(shape(feature['geometry']), feature['properties'])
                  for feature in json.loads(data)['features'] if feature.get('geometry')]
        if not result:
            raise RoutingDataError(f'{name} has no geometry')
        return result
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise RoutingDataError(f'{name} could not be loaded') from exc


@cache
def city_geometry():
    city = unary_union([geometry for geometry, _ in features('gainesville.geojson', META['sha256'])])
    return city, transform(project, city)


@cache
def street_index():
    streets = features('streets.geojson', META['streets']['sha256'])
    return STRtree([transform(project, geometry) for geometry, _ in streets]), [props for _, props in streets]


def boundary(location):
    if not location:
        return 'outside'
    try:
        city, metric = city_geometry()
        point = Point(location['longitude'], location['latitude'])
        if transform(project, point).distance(metric.boundary) <= max(10, location.get('accuracy') or 0):
            return 'boundary_uncertain'
        return 'inside' if city.contains(point) else 'outside'
    except LOOKUP_ERRORS as exc:
        logger.warning('Gainesville boundary lookup failed (%s)', type(exc).__name__)
        return 'boundary_lookup_failed'


def unresolved(route, code, guidance):
    return {**route, 'reason_codes': [code], 'guidance': guidance}


def lookup_failed(route):
    return {**unresolved(route, 'destination_lookup_failed', LOOKUP_FAILED_GUIDANCE), 'status': 'error'}


def resolved(route, destination):
    return {
        **route,
        'status': 'resolved',
        'route_id': destination['route_id'],
        'jurisdiction': destination['jurisdiction'],
        'destination_name': destination['name'],
        'portal_url': destination['destination'],
        'source_urls': [destination['source'], *route['source_urls']],
        'guidance': destination.get('guidance'),
    }


def road_destination(route, location, category):
    route['source_urls'].append(META['streets']['source'])
    try:
        tree, streets = street_index()
        pin = transform(project, Point(location['longitude'], location['latitude']))
        nearest = tree.nearest(pin)
        distance = pin.distance(tree.geometries[nearest])
        if distance > ROAD_MATCH_METRES:
            name = streets[nearest].get('FULL_NAME')
            if name and distance <= NEARBY_ROAD_METRES:
                route['road_names'] = [name]
            return unresolved(route, 'road_location_required',
                              f'The pin is too far from a mapped road to identify the affected roadway. {ROAD_LOCATION_GUIDANCE}')

        # A confirmed GPS pin can still cover several roads with different maintainers.
        radius = max(ROAD_MATCH_METRES, location.get('accuracy') or 0)
        candidates = tree.query(pin, predicate='dwithin', distance=radius)
        roads = [streets[index] for index in candidates]
    except LOOKUP_ERRORS as exc:
        logger.warning('Street destination lookup failed (%s)', type(exc).__name__)
        return lookup_failed(route)

    route['road_names'] = sorted({road['FULL_NAME'] for road in roads if road.get('FULL_NAME')})
    maintainers = {road.get('MAINTBY') or None for road in roads}
    if len(maintainers) > 1:
        return unresolved(route, 'road_maintainer_conflict',
                          'Nearby road segments have different maintenance records. '
                          'Place the pin on the affected street just away from the intersection and enter '
                          'which street has the issue and its nearest cross street.')
    maintainer = next(iter(maintainers), None)
    if maintainer is None:
        return unresolved(route, 'road_maintainer_unlisted',
                          'The street inventory has no maintenance agency for this pin. '
                          'Confirm the affected street and nearest cross street with Gainesville Public Works.')
    destinations = META['reporting_rules']['pothole']['maintainers']
    if maintainer in destinations and (category == 'pothole' or maintainer == CITY_MAINTAINER):
        return resolved(route, destinations[maintainer])
    return unresolved(route, 'road_intake_unverified',
                      f'The street inventory lists {maintainer} as the maintainer. Contact that agency '
                      'with the affected street and nearest cross street for reporting guidance.')


def resolve(location, category):
    route = {
        'status': 'unresolved', 'route_id': None, 'jurisdiction': None, 'destination_name': None,
        'portal_url': None, 'rules_version': RULES_VERSION, 'boundary_version': BOUNDARY_VERSION,
        'source_urls': [META['boundary_source']], 'verified_at': META['routing_verified_at'],
        'reason_codes': [], 'road_names': [],
    }
    if not location:
        return unresolved(route, 'missing_location', 'Pin the issue location in Gainesville.')
    if not location.get('confirmed'):
        return unresolved(route, 'unconfirmed_location', 'Confirm the issue location before checking the destination.')
    status = boundary(location)
    if status == 'boundary_lookup_failed':
        return lookup_failed(route)
    if status == 'boundary_uncertain':
        return unresolved(route, status, 'Place the pin more precisely on the Gainesville side of the city boundary.')
    if status != 'inside':
        return unresolved(route, 'outside_service_area', 'This location is outside CivicFix’s Gainesville service area.')
    if not category:
        return unresolved(route, 'missing_category', 'Select an issue category so CivicFix can check the destination.')
    if category == 'leaking_hydrant':
        route['source_urls'] = [META['reporting_rules'][category]['source']]
        return unresolved(route, 'no_verified_online_form', 'Contact GRU for hydrant and water-leak reporting guidance.')
    if category == 'broken_streetlight':
        route['source_urls'] = [GRU_GUIDE]
        return unresolved(route, 'unknown_ownership',
                          'Verify the pole owner and whether the issue is an outage or physical damage. '
                          'GRU can help identify the right reporting channel.')
    if category in ('pothole', 'damaged_sign'):
        return road_destination(route, location, category)
    return resolved(route, META['reporting_rules']['pothole']['maintainers'][CITY_MAINTAINER])
