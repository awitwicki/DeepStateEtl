from pyproj import Geod
import json
import requests
import os
import time
import numpy as np

def download_file(file_url, save_path):
    response = requests.get(file_url)
    
    if response.status_code == 200:
        with open(save_path, "wb") as file:
            file.write(response.content)
        
        return save_path
    else:
        raise Exception(f"Error with file download: {response.status_code}")


def read_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def calculate_polygon_area_km2(geojson_feature_data):
    geod = Geod(ellps="WGS84")

    coordinates = geojson_feature_data["geometry"]["coordinates"][0]

    lons, lats, _ = zip(*coordinates)

    area_m2, _perimeter = geod.polygon_area_perimeter(lons, lats)

    area_km2 = abs(area_m2) / 1_000_000
    return area_km2


def calculate_area_from_file(geojson_path):
    geojson_data = read_json_file(geojson_path)
    total_area_km2 = 0

    for feature in geojson_data.get("features", []):
        properties = feature.get("properties", {})
        if 'geoJSON.status.occupied' in properties.get("name"):
            area_km2 = calculate_polygon_area_km2(feature)
            total_area_km2+=area_km2

    return total_area_km2


def download_json_geodata_from_item(json_data, sleep_seconds):
    data_id = json_data['id']
    created_ad = json_data['createdAt'].split('.')[0]
    download_file_name = f'data/{created_ad}.json'
    download_url = f'https://deepstatemap.live/api/history/{data_id}/geojson'

    if os.path.exists(download_file_name):
        return
    download_file(download_url, download_file_name)
    time.sleep(sleep_seconds)


def smooth_data(data, window_size=7):
    values = list(data.values())

    smoothed = []
    deltas = []

    for i in range(len(values)):
        start = max(0, i - window_size // 2)
        end = min(len(values), i + window_size // 2 + 1)
        smoothed_value = np.mean(values[start:end])
        smoothed.append(smoothed_value)

        if i > 0:
            delta = smoothed_value - smoothed[i - 1]
        else:
            delta = 0

        if delta > 1000:
            delta = start
        deltas.append(delta)

    return deltas, list(data.keys())
