from flask import Flask, render_template, url_for, request, redirect
import json
import requests
import sys
import argparse
import os

app = Flask(__name__)
app.url_map.strict_slashes = False

dirname = os.path.dirname(__file__)
__services_config_file = (dirname + '/' if dirname else '') + '../../cfg/services.json'
config = json.load(open(__services_config_file))


@app.route('/')
def index():
    return redirect('/routes')
    #return render_template('index.html')


@app.route('/map3d')
def get_3d_map():
    try:
        route_config = config['map_3d']
        map_3d = get(route_config)
    except requests.exceptions.HTTPError as exception:
        return exception.text, exception.errno
    except requests.exceptions.ConnectionError:
        return '3D Map service unavailable', 503
    return render_template('layout.html', html=map_3d)


@app.route('/routes/<routeid>/3d')
def get_3d_map_by_routeid(routeid):
    try:
        route_config = config['map_3d']
        map_3d = get(route_config)
    except requests.exceptions.HTTPError as exception:
        return exception.text, exception.errno
    except requests.exceptions.ConnectionError:
        return '3D Map service unavailable', 503
    return render_template('layout.html', html=map_3d)


# called like localhost:5000/map2d?id=000910&start_time=1500&end_time=2000
@app.route('/map2d')
def get_2d_map():
    '''id = request.args.get('id')
    start_time = request.args.get('start')
    end_time = request.args.get('end')'''
    try:
        route_config = config['map_2d']
        map_2d = get(route_config)
    except requests.exceptions.HTTPError as exception:
        return exception.text, exception.errno
    except requests.exceptions.ConnectionError:
        return '2D Map service unavailable', 503
    return render_template('layout.html', html=map_2d)


@app.route('/routes/<routeid>/2d')
def get_2d_map_by_routeid(routeid):
    try:
        route_config = config['map_2d']
        map_2d = get(route_config)
    except requests.exceptions.HTTPError as exception:
        return exception.text, exception.errno
    except requests.exceptions.ConnectionError:
        return '2D Map service unavailable', 503
    return render_template('layout.html', html=map_2d)


@app.route('/routes', methods = ['GET', 'POST', 'DELETE'])
def routes():
    route_config = config['drone_information']
    try:
        if request.method == 'GET':
            return get_drone_routes_list(route_config)

        elif request.method == 'POST':
            return post_drone_route(route_config)

        elif request.method == 'DELETE':
            return delete_drone_route(route_config)
    except requests.exceptions.HTTPError as exception:
        return exception.text, exception.errno
    except requests.exceptions.ConnectionError:
        return 'Drone information service unavailable', 503


def get_drone_routes_list(route_config):
    drone_routes_list = json.loads(get(route_config))
    return render_template('route_list.html', drones=drone_routes_list)


def post_drone_route(route_config):
    return post(route_config)


def delete_drone_route(route_config):
    return delete(route_config)


def get(route_config):
    url = get_url_string(route_config)
    response = requests.get(url)
    raise_for_status_code(response)
    return response.text


def post(route_config):
    url = get_url_string(route_config)
    response = requests.post(url, json=request.json)
    raise_for_status_code(response)
    return response.text


def delete(route_config):
    url = get_url_string(route_config)
    response = requests.delete(url, json=request.json)
    raise_for_status_code(response)
    return response.text


def get_url_string(route_config):
    url = 'http://{}:{}{}'
    if(request.remote_addr == '127.0.0.1'):
        url = url.format('127.0.0.1', route_config['port'], request.path)
    else:
        url = url.format(route_config['host'], route_config['port'], request.path)
    return url


def raise_for_status_code(response):
    if not response:
        exception = requests.exceptions.HTTPError(response.status_code, response.reason)
        exception.text = response.text
        raise exception


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', type=str, default='0.0.0.0',
                        help='specify which host to run this service on')
    parser.add_argument('-p', '--port', type=int, default=5000,
                        help='specify which port to run this service on')
    parser.add_argument('-v', '--version', type=float, default=0,
                        help='specify which version of the service this is')
    args = parser.parse_args()
    args.prog = sys.argv[0].split('/')[-1].split('.')[0]

    print('Running {} service version {}'.format(args.prog, args.version))
    os.system('title {} service version {} on {}:{}'.format(
        args.prog, args.version, args.address, args.port))
    app.run(host=args.address, port=args.port, debug=True, threaded=True)
