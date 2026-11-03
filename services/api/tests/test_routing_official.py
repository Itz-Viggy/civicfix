from civicfix.routing import boundary,resolve,CITY

def location(**kw):return dict(latitude=29.645781879176276,longitude=-82.30619912751014,confirmed=True,**kw)
def test_official_inside_outside_edge():
    assert boundary(location())=='inside'
    assert boundary(dict(latitude=30,longitude=-83))=='outside'
    x,y=list(CITY.geoms)[0].exterior.coords[0] if hasattr(CITY,'geoms') else CITY.exterior.coords[0]
    assert boundary(dict(latitude=y,longitude=x))=='boundary_uncertain'
def test_ownership_and_form_limits():
    assert resolve(location(),'pothole')['status']=='resolved'
    assert resolve(location(),'damaged_sign')['status']=='resolved'
    assert resolve(location(),'leaking_hydrant')['reason_codes']==['no_verified_online_form']
    assert resolve(location(),'broken_streetlight')['reason_codes']==['unknown_ownership']
    assert resolve(location(accuracy=100000),'pothole')['status']=='unresolved'
