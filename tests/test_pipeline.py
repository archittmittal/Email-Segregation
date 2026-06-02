from __future__ import annotations
import pytest
from classification.classifier import classify
from extraction.tonnage_extractor import extract_tonnage
from extraction.cargo_vc_extractor import extract_cargo_vc
from extraction.cargo_tc_extractor import extract_cargo_tc
from routes.matching import _port_score, _size_score, _date_score, _parse_dwt, _parse_quantity
from routes.emails import _fingerprint

def test_classifier():
    # Tonnage text
    tonnage_text = "OUR DIRECT OWS OPEN AS FOLLOWS: MV SARONIC CHAMPION DWT 93000 OPEN VUNG ANG 08-12 JUNE"
    cat, conf = classify(tonnage_text)
    assert cat == "tonnage"
    assert conf > 0.4

    # Cargo VC text
    vc_text = "LOAD PORT: KOH SI CHANG, DISCHARGE PORT: KANDLA, LAYCAN: MID JULY, 20000 MTS COAL"
    cat, conf = classify(vc_text)
    assert cat == "cargo_vc"

    # Cargo TC text
    tc_text = "A/C SeaSchiffe, 1 TCT with Steels, Delivery: ECI, Laycan: 15-18 July, Redel: Med"
    cat, conf = classify(tc_text)
    assert cat == "cargo_tc"


def test_tonnage_extractor():
    text = "MV SARONIC CHAMPION DWT 93000 OPEN VUNG ANG O/A 08-12 JUNE"
    vessels = extract_tonnage(text, 1)
    assert len(vessels) == 1
    v = vessels[0]
    assert v["vessel_name"] == "SARONIC CHAMPION"
    assert "93000" in v["vessel_size"]
    assert v["open_port"] == "VUNG ANG"
    assert v["open_date"] == "08-12 JUNE"


def test_cargo_vc_extractor():
    text = """
    15,000 - 20,000 MTS COAL
    LOAD PORT: KOH SI CHANG
    DISCHARGE PORT: KANDLA
    LAYCAN: MID JULY 2026
    """
    cargos = extract_cargo_vc(text, 1)
    assert len(cargos) == 1
    c = cargos[0]
    assert c["cargo_name"] == "COAL"
    assert c["loading_port"] == "KOH SI CHANG"
    assert c["discharge_port"] == "KANDLA"
    assert c["laycan"] == "MID JULY 2026"
    assert "15,000" in c["quantity"]


def test_cargo_tc_extractor():
    text = """
    * Delivery: ECI
    * Laycan: 15-18 July
    * Redel: Med via GOA
    * Duration: abt 35-40 days wog
    * 1 TCT with Steels
    """
    cargos = extract_cargo_tc(text, 1)
    assert len(cargos) == 1
    c = cargos[0]
    assert c["delivery_port"] == "ECI"
    assert c["redelivery_port"] == "Med via GOA"
    assert c["duration"] == "35-40 days"
    assert c["laycan"] == "15-18 July"
    assert c["cargo_name"] == "Steels"


def test_matching_scores():
    # Exact port match
    assert _port_score("Kandla", "Kandla") == 50
    # Token prefix match
    assert _port_score("Kandla Port", "Kandla") == 35
    
    # Size score
    assert _size_score("50000 DWT", "45000 MTS") == 20
    
    # DWT parsing checks
    assert _parse_dwt("93.116 DWT") == 93116.0
    assert _parse_dwt("56K DWT") == 56000.0
    assert _parse_dwt("56000") == 56000.0
    
    # Quantity parsing checks
    assert _parse_quantity("15,000 - 20,000 MTS 10PCT") == 17500.0
    
    # Date score
    from datetime import datetime
    current_year = datetime.now().year
    assert _date_score(f"OPEN XIAMEN O/A 2ND JUNE {current_year}", "LC 10-17 JUNE") == 30


def test_deduplication():
    t1 = "Hello, this is a test email body for deduplication checking."
    t2 = "hello,  this is a test email body for deduplication checking. "
    assert _fingerprint(t1) == _fingerprint(t2)


def test_analytics_endpoint():
    from app import app
    with app.test_client() as client:
        response = client.get('/api/analytics')
        assert response.status_code == 200
        data = response.json
        assert 'total_emails' in data
        assert 'tonnage_records' in data
        assert 'cargo_vc_records' in data
        assert 'cargo_tc_records' in data
        assert 'trend' in data
        assert 'top_ports' in data
        assert 'vessel_sizes' in data
        
        # Check trend structure
        assert 'labels' in data['trend']
        assert 'series' in data['trend']
        assert len(data['trend']['labels']) == 30
        assert 'tonnage' in data['trend']['series']
        assert 'cargo_vc' in data['trend']['series']
        assert 'cargo_tc' in data['trend']['series']
        
        # Check top_ports structure
        assert 'labels' in data['top_ports']
        assert 'data' in data['top_ports']
        
        # Check vessel_sizes structure
        assert 'labels' in data['vessel_sizes']
        assert 'data' in data['vessel_sizes']

