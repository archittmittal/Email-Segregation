"""Dispatcher: routes to the correct extractor and saves records."""
from extraction.tonnage_extractor import extract_tonnage
from extraction.cargo_vc_extractor import extract_cargo_vc
from extraction.cargo_tc_extractor import extract_cargo_tc
from database.models import Tonnage, CargoVC, CargoTC


def extract(category: str, text: str, email_id: int, session) -> list[dict]:
    """Extract structured data, persist to DB, return list of extracted dicts."""
    records = []

    if category == 'tonnage':
        vessels = extract_tonnage(text, email_id)
        for v in vessels:
            obj = Tonnage(**v)
            session.add(obj)
            records.append(v)

    elif category == 'cargo_vc':
        cargos = extract_cargo_vc(text, email_id)
        for c in cargos:
            obj = CargoVC(**c)
            session.add(obj)
            records.append(c)

    elif category == 'cargo_tc':
        cargos = extract_cargo_tc(text, email_id)
        for c in cargos:
            obj = CargoTC(**c)
            session.add(obj)
            records.append(c)

    return records
