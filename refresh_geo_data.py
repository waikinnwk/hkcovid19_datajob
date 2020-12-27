from api_config import *
import requests
import time
import json
from datetime import datetime
import os

header = {
"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
"X-Requested-With": "XMLHttpRequest"
} 

log_datetime_format = "%A, %d. %B %Y %I:%M:%S %p"
data_date_format = "%Y-%m-%d"


def default(obj):
    """Default JSON serializer."""
    import calendar, datetime

    if isinstance(obj, datetime.datetime):
        if obj.utcoffset() is not None:
            obj = obj - obj.utcoffset()
        millis = int(
            calendar.timegm(obj.timetuple()) * 1000 +
            obj.microsecond / 1000
        )
        return millis
    raise TypeError('Not sure how to serialize %s' % (obj,))


def refresh_geo_data():
    print("refresh_geo_data start :" + time.strftime(log_datetime_format))
    get_related_building_url = os.environ.get('GET_RELATED_BUILDING_URL')
    if get_related_building_url is None:
        get_related_building_url = 'http://localhost:8091/hkcovid19caserelatedbuilding/getLatest'
    res = requests.post(get_related_building_url, headers=header)
    buildings = res.json()

    print("refresh_geo_data - finish get all building :" + time.strftime(log_datetime_format))
    check_has_coordinate_url = os.environ.get('CHECK_HAS_COORDINATE_URL')
    if check_has_coordinate_url is None:
        check_has_coordinate_url = 'http://localhost:8090/buildinglocation/hasCoordinate'


    url_getxy_hkgov ="https://geodata.gov.hk/gs/api/v1.0.0/locationSearch?q="
    url_xy_to_lat_lon_hkgov = "http://www.geodetic.gov.hk/transform/v2/?inSys=hkgrid"
    url_getxy_openstreetmap_pre = "https://nominatim.openstreetmap.org/search?q="
    url_getxy_openstreetmap_post = "&format=json&polygon=1&addressdetails=1" 

    add_coordinate_url = os.environ.get('ADD_COORDINATE_URL')
    if add_coordinate_url is None:
        add_coordinate_url = 'http://localhost:8090/buildinglocation/add'

    inserted = 0
    for building in buildings:
        data_obj = {'district' : building['district'], 'buildingName':building['buildingName'],'lat' :0.0,'lon':0.0}
        res = requests.post(check_has_coordinate_url, json=data_obj, headers=header)
        has_coordinate = res.json()
        print(building['buildingName'] + ' ' + has_coordinate['result'])
        if has_coordinate['result'] == 'N':
            print("refresh_geo_data - start update Coordinate")
            try:
                lat = None
                lon = None
                map_request_starttime = datetime.now()
                response = requests.get(url_getxy_hkgov+building['buildingName']+","+building['district'],data = [], headers=header)
                json_data = response.json()
                if len(json_data) > 0:           
                    for data in json_data:
                        x = data["x"]
                        y = data["y"]
                        print('x :' + str(x) +' , y :' + str(y))
                        xy_response = requests.get(url_xy_to_lat_lon_hkgov+"&e="+str(x)+"&n="+str(y),data = [], headers=header)
                        xy_json_data = xy_response.json()
                        if len(xy_json_data) > 0:           
                            lon = xy_json_data["wgsLong"]
                            lat = xy_json_data["wgsLat"]                               
                        break
                else:
                    response = requests.get(url_getxy_openstreetmap_pre+building['buildingName']+","+building['district']+url_getxy_openstreetmap_post,data = [], headers=header)
                    json_data = response.json()
                    if len(json_data) > 0:           
                        for data in json_data:
                            lon = data["lon"]
                            lat = data["lat"]
                            break
                    else:
                        print("No result from Open Street Map & Gov Map " + building['buildingName'] +","+building['district'])
                print('lon :' + str(lon) +' , lat :' + str(lat))
                
                new_data_obj = {"district":building['district'],
                "buildingName":building['buildingName'],
                "lat": lat,
                "lon": lon}
                response = requests.post(add_coordinate_url,json = new_data_obj, headers=header)
                inserted+=1
                               
            except Exception as e: print(e)
            if inserted >= 150:
                break
            else:
                map_request_endtime = datetime.now()
                difference = (map_request_endtime - map_request_starttime)
                total_seconds = difference.total_seconds()        
                if total_seconds < 1:
                    time.sleep(1)

    print("refresh_geo_data end :" + time.strftime(log_datetime_format))

refresh_geo_data()