from flask import Flask, render_template, url_for, request, jsonify
from models import Drone, Route
from interpolator import spline_interpolate
from time_util import epoch_to_datetime, epoch_to_time
import requests
import json
import sys
import argparse
import os

__config_file = os.path.realpath(__file__) + '/../cfg/config.json'
config = json.load(open(__config_file))
db_config = config['db']

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}:{}/{}'.format(db_config['user'], db_config['password'], db_config['host'], db_config['port'], db_config['database'])
app.config['SQLALCHEMY_POOL_SIZE'] = 100
app.config['SQLALCHEMY_POOL_RECYCLE'] = 280
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

interpolation_interval = config['interpolation_interval']


@app.route('/')
def index():
    func_list = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            func_list[rule.rule] = app.view_functions[rule.endpoint].__doc__
    return jsonify(func_list)


#SELECT * FROM routes_end
#routes_end, for så får vi de ruter der ER færdige
'''def get_drone_info():
    list_of_drone_dicts = []
    drone_info = requests.get('https://droneid.dk/bsc2018/droneid.php').text.strip('\n')
    if drone_info:
        for row in drone_info.splitlines():
            data = row.split(',')
            list_of_drone_dicts.append({
                'time_stamp': data[0],
                'time': data[1], 
                'id': data[2], 
                'name': data[3], 
                'lat': data[4],
                'lon': data[5], 
                'alt': data[6], 
                'acc': data[7], 
                'fix': data[8], 
                'lnk': data[9], 
                'eng': data[10], 
                'sim': data[11]
            })
    return list_of_drone_dicts'''

@app.route('/list')
def list_drones():
    '''Returns a list of all drone routes'''
    #drone = db.session.query(Drone.lon).filter_by(id='501').filter(Drone.time >= 1521712566, Drone.time <= 1521712581).all()
    #drone = db.session.query(Route_end.id, Route_end.end_time).all()
    #userList = users.query.join(friendships, users.id==friendships.user_id).add_columns(users.userId, users.name, users.email, friends.userId, friendId).filter(users.id == friendships.friend_id).filter(friendships.user_id == userID).paginate(page, 1, False)
    #drone_routes = Route_end.query.join(Route_start, Route_end.id==Route_start.id).add_columns(Route_start.start_time).all()
    
    #drone_routes_results = db.session.query(Route_end.id, Route_end.end_time).join(Route_start, Route_end.id==Route_start.id).add_columns(Route_start.start_time).all()
    list_of_drone_dicts = result_to_list_of_dicts(db.session.query(Route.route_id, Route.drone_id.label('id'), Route.start_time, Route.end_time).filter(Route.end_time != None).all())
    
    for drone_dict in list_of_drone_dicts:
        drone_dict['start_time_stamp'] = epoch_to_datetime(drone_dict['start_time'])
        drone_dict['end_time_stamp'] = epoch_to_datetime(drone_dict['end_time'])
        drone_dict['duration'] = epoch_to_time(drone_dict['end_time'] - drone_dict['start_time'])
    return jsonify(list_of_drone_dicts)


@app.route('/<id>/<start_time>/<end_time>')
def route_with_params(id, start_time, end_time):
    '''Returns list of coordinates and drone information, for the route that corresponds to the provided id, start time and end time'''
    list_of_drone_dicts = result_to_list_of_dicts(db.session.query(Drone.id, Drone.time, Drone.time_stamp, Drone.lat, Drone.lon, Drone.alt).filter(Drone.id == id, Drone.time >= start_time, Drone.time <= end_time).all())
    return jsonify(list_of_drone_dicts)


@app.route('/<id>/<start_time>/<end_time>/interpolated')
def route_with_params_interpolated(id, start_time, end_time):
    '''Returns list of interpolated (2 seconds) coordinates and drone information, for the route that corresponds to the provided id, start time and end time. Interpolation requires more than 3 coordinates.'''
    list_of_drone_dicts = result_to_list_of_dicts(db.session.query(Drone.id, Drone.time, Drone.time_stamp, Drone.lat, Drone.lon, Drone.alt).filter(Drone.id == id, Drone.time >= start_time, Drone.time <= end_time).all())
    if len(list_of_drone_dicts) > 3:
        list_of_drone_dicts = spline_interpolate(list_of_drone_dicts, interpolation_interval)
    return jsonify(list_of_drone_dicts)


def result_to_list_of_dicts(results):
    list_of_dicts = []
    for result in results:
        list_of_dicts.append(
            dict(zip(result.keys(), result))
        )
    return list_of_dicts


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', type=str, default='127.0.0.1',
                        help='specify which host to run this service on')
    parser.add_argument('-p', '--port', type=int, default=5001,
                        help='specify which port to run this service on')
    parser.add_argument('-v', '--version', type=float, default=0,
                        help='specify which version of the service this is')
    args = parser.parse_args()
    args.prog = sys.argv[0].split('/')[-1].split('.')[0]

    print('Running {} service version {}'.format(args.prog, args.version))
    os.system('title {} service version {} on {}:{}'.format(
        args.prog, args.version, args.address, args.port))
    app.run(host=args.address, port=args.port, debug=True, threaded=True)
