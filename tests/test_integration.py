import pytest
from flask import request
import requests
import sys
import os
import json
import time
from multiprocessing import Process
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from services.api_gateway import api_gateway
from services.drone_information import drone_information
from scripts.util import config


@pytest.fixture
def app_client():
    api_gateway.app.config['TESTING'] = True
    api_gateway.config = json.load(open(api_gateway.__services_config_file))
    app_client = api_gateway.app.test_client()
    yield app_client


def test_drone_information_end_to_end(app_client):
    response = app_client.get('/routes')
    assert response.status_code == 503
    assert response.data.decode().strip() == 'Drone information service unavailable'

    server = start_server(__run_drone_information, config['drone_information']['port'])
    
    response = app_client.get('/routes')
    assert response.status_code == 200

    stop_server(server)


def test_drone_information_integration():
    with api_gateway.app.test_request_context():
        with pytest.raises(requests.exceptions.ConnectionError):
            api_gateway.get('drone_information', '/')

        server = start_server(__run_drone_information, config['drone_information']['port'])
        
        assert api_gateway.get('drone_information', '/')

        stop_server(server)


def test_different_ports_for_same_service(app_client):
    server_1 = start_server(__run_drone_information, config['drone_information']['port'])
    
    response = app_client.get('/routes')
    assert response.status_code == 200

    stop_server(server_1)

    new_port = 6001
    server_2 = start_server(__run_drone_information, new_port)
    
    api_gateway.config = {
        'drone_information': {
            'host': '127.0.0.1', 
            'port': new_port + 1
        }
    }
    response = app_client.get('/routes')
    assert response.status_code == 503
    assert response.data.decode().strip() == 'Drone information service unavailable'

    api_gateway.config = {
        'drone_information': {
            'host': '127.0.0.1', 
            'port': new_port
        }
    }
    response = app_client.get('/routes')
    assert response.status_code == 200

    stop_server(server_2)


def start_server(service, port):
    server = Process(target=service, args=[port])
    server.daemon = True
    server.start()
    time.sleep(1)
    return server


def stop_server(server):
    server.terminate()
    server.join()


def __run_drone_information(port):
    drone_information.app.run(host='127.0.0.1', port=port, debug=False, threaded=False)


if __name__ == '__main__':
    pytest.main()