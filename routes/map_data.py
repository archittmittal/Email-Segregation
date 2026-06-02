from flask import Blueprint, jsonify
from database.db import get_session
from database.models import Tonnage, CargoVC, CargoTC

map_data_bp = Blueprint('map_data', __name__)

# Zero-API Dictionary of Major Global Ports
PORTS_DB = {
    "KANDLA": {"lat": 23.0333, "lon": 70.2167},
    "VUNG ANG": {"lat": 18.0667, "lon": 106.3833},
    "SINGAPORE": {"lat": 1.2902, "lon": 103.8519},
    "ROTTERDAM": {"lat": 51.9225, "lon": 4.4791},
    "HOUSTON": {"lat": 29.7604, "lon": -95.3698},
    "SHANGHAI": {"lat": 31.2304, "lon": 121.4737},
    "DURBAN": {"lat": -29.8587, "lon": 31.0218},
    "SANTOS": {"lat": -23.9619, "lon": -46.3336},
    "FUJAIRAH": {"lat": 25.1164, "lon": 56.3414},
    "ANTWERP": {"lat": 51.2194, "lon": 4.4025},
    "NEW ORLEANS": {"lat": 29.9511, "lon": -90.0715},
    "QINGDAO": {"lat": 36.0671, "lon": 120.3826},
    "JEBEL ALI": {"lat": 24.9857, "lon": 55.0273},
    "BUSAN": {"lat": 35.1796, "lon": 129.0756},
    "HAMBURG": {"lat": 53.5511, "lon": 9.9937},
    "LOS ANGELES": {"lat": 34.0522, "lon": -118.2437},
    "RICHARDS BAY": {"lat": -28.7807, "lon": 32.0383},
    "MUMBAI": {"lat": 18.9667, "lon": 72.8333},
    "PARADIP": {"lat": 20.2667, "lon": 86.6667},
    "HALDIA": {"lat": 22.0333, "lon": 88.0667},
    "VISAKHAPATNAM": {"lat": 17.6883, "lon": 83.2186},
    "ECI": {"lat": 16.5, "lon": 82.0},
    "WCI": {"lat": 19.0, "lon": 72.5},
    "MED": {"lat": 35.0, "lon": 15.0},
    "GOA": {"lat": 15.2993, "lon": 73.9690},
    "KOH SI CHANG": {"lat": 13.1533, "lon": 100.8142},
    "SUEZ": {"lat": 29.9668, "lon": 32.5498},
    "PANAMA": {"lat": 8.9833, "lon": -79.5167},
}

def find_coordinates(port_name):
    if not port_name:
        return None
    port_name = str(port_name).upper()
    for key, coords in PORTS_DB.items():
        if key in port_name:
            return coords
    return None

@map_data_bp.route('/map', methods=['GET'])
def get_map_data():
    session = get_session()
    markers = []

    # 1. Fetch Tonnage
    for t in session.query(Tonnage).order_by(Tonnage.created_at.desc()).limit(100).all():
        coords = find_coordinates(t.open_port)
        if coords:
            markers.append({
                "type": "tonnage",
                "lat": coords["lat"],
                "lon": coords["lon"],
                "title": t.vessel_name or "Unknown Vessel",
                "subtitle": f"Open: {t.open_port}",
                "date": t.open_date or ""
            })

    # 2. Fetch Cargo VC
    for c in session.query(CargoVC).order_by(CargoVC.created_at.desc()).limit(100).all():
        coords = find_coordinates(c.load_port)
        if coords:
            markers.append({
                "type": "cargo_vc",
                "lat": coords["lat"],
                "lon": coords["lon"],
                "title": c.cargo_name or "Unknown Cargo",
                "subtitle": f"Load: {c.load_port}",
                "date": c.laycan or ""
            })

    # 3. Fetch Cargo TC
    for c in session.query(CargoTC).order_by(CargoTC.created_at.desc()).limit(100).all():
        coords = find_coordinates(c.delivery_port)
        if coords:
            markers.append({
                "type": "cargo_tc",
                "lat": coords["lat"],
                "lon": coords["lon"],
                "title": c.cargo_type or "Unknown Cargo TC",
                "subtitle": f"Delivery: {c.delivery_port}",
                "date": c.laycan or ""
            })
            
    session.close()
    return jsonify({"markers": markers})
