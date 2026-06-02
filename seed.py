"""
seed.py — Pre-populate the database with the real sample emails provided.
Run automatically during Render build: `python seed.py`
Also safe to re-run (skips if DB already has data).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db, get_session
from database.models import Email
from classification.classifier import classify
from extraction.extractor import extract

init_db()

# ── Sample emails (real data from Prime Maritime & brokers) ──────────────────

SAMPLE_EMAILS = [
    {
        "subject": "PRIME MARITIME – OPEN VESSELS PACIFIC – 25 MAY 2026",
        "sender": "chartering@primemaritime.gr",
        "text": """PRIME MARITIME INC. - PIRAEUS
GOOD DAY
OUR DIRECT OWS OPEN AS FOLLOWS
PLS PPSE SUIT
PACIFIC
SARONIC CHAMPION (93K – SCRUBBER FITTED / 2011 ) – OPEN VUNG ANG, VIETNAM 08-12 JUNE

SARONIC CHAMPION
LIBERIA FLAG
BUILT 2011
CLASS LR
ABT 93.116 DWT ON ABT 14.90 MTRS SSW
LOA 229.253 MTRS / BEAM 38.00 MTRS
GRAIN CAP ABT 110.330 CBM
7/7 HO/HA – SCRUBBER FITTED
SPEED / CONS (INCLUDING A/E)
BALLAST : ABT 12.75 KNOTS ON ABT 30.50 MTS IFO 380 CST
LADEN : ABT 11.75 KNOTS ON ABT 30.50 MTS IFO 380 CST

BEST REGARDS
GEORGE RACHIOTIS""",
    },
    {
        "subject": "OPEN TONNAGE LIST – PACIFIC & INDIAN OCEAN – 25 MAY 2026",
        "sender": "chartering@chinashipping.com",
        "text": """GOOD DAY,
PLS PROPOSE FOR THE BELOW TONNAGE LIST:

PACIFIC OCEAN
MV SHENG AN HAI DWT 56564 OPEN XIAMEN, CHINA O/A 2ND JUNE 2026
MV FENG HUI HAI DWT 63260 OPEN GUANGZHOU, CHINA O/A 6TH JUNE 2026
MV YUANPING SEA DWT 55646 OPEN MANILA, PHI O/A 3RD JUNE 2026
MV SHENG DE HAI DWT 56721 OPEN SAMALAJU, MALAYSIA O/A 3RD JUNE 2026

INDIAN OCEAN
MV YIN HUA 1 DWT 46613 OPEN CHITTAGONG, B.DESH O/A 5TH JUNE 2026
MV BI JIA SHAN DWT 56623 OPEN GWADAR, PAKISTAN O/A 2ND JUNE 2026
MV YUANNING SEA DWT 55580 OPEN SOHAR, OMAN O/A 30TH MAY 2026
MV COS ORCHID DWT 55550 OPEN DAR ES SALAAM, TANZANIA O/A 1ST JUNE 2026

VSL PARTICULAR:
MV SHENG AN HAI
BUILT: 2012
FLAG: CHINA
CLASS: CCS
DWT 56564.4MT ON 12.8M SSW
LOA 189.99M / BEAM 32.26M
5 HO/5 HA
GRAIN 71634.09CBM

------------------------------

MV FENG HUI HAI
2017 BLT HONG KONG FLAG SDSTBC
63260.8 DWT ON 13.30M SSW
LOA/BEAM 199.9/32.26M
5 HO/5 HA
GRAIN/BALE CAPACITY 78771.0/73430CBM
4 X 30 TON CRANES AND 4 X 12 CMB GRAB

------------------------------

MV YIN HUA 1
2013 BLT CHINA FLAG SDBC
CLASS: CCS
DWT 46613 MT ON 10.90M SSW
LOA/BEAM 189.99/32.26
5 HO/5 HA
60276.1 CBM GRAIN
4X36T CRANE

------------------------------

MV BI JIA SHAN
HONG KONG FLAG SDBC
56625 MTDW ON 12.80M SSW
LOA/BM 189.99/32.26M
5HO/5HA  GRABS 4X12.0 CBM
CRANE 4X30T

------------------------------

MV YUANNING SEA
2004 BLT PANAMA FLAG SDSTBC
55580DWT ON 12.52M SSW
LOA/BEAM 189.94/32.26M
5 HO/5 HA
4 X 30TON CRANES

------------------------------

MV COS ORCHID
DWT 55550MT DRAFT OF 12.5M SSW
BUILT 2006
SINGAPORE FLAG SDBC
LOA/BEAM 189.9/32.26M
5 HO/HA  4X30T CRANE/GRAB 4X12CUM

END""",
    },
    {
        "subject": "PRIME MARITIME – MV TRUE FRIEND – OPEN BEJAIA 1ST JUNE",
        "sender": "chartering@primemaritime.gr",
        "text": """PRIME MARITIME INC. - PIRAEUS
GOOD DAY
OUR CLOSE OWS OPEN ASF
MV TRUE FRIEND/51K/09 - BEJAIA, 1ST JUNE ONW - EX OUR CP

MV TRUE FRIEND
DWT: 51,241
BUILT: 2009
FLAG: BARBADOS
BULK CARRIER
CLASSIFICATION: NK
GROSS TONNAGE: 30,655
LOA: 182.98M
5/5 HO/HA
GRAIN: ABT 59,676

SPEED/CONSUMPTION:
ECO SP&CO
11.0K@21.5 MT/(BALLAST)&0.25MGO
11.0K@22.0 MT (LADEN)&0.25MGO

BEST REGARDS
KOSTAS SOTIROPOULOS""",
    },
    {
        "subject": "MV BLUE STAR 38K – OPEN GABES TUNISIA 25 MAY",
        "sender": "chartering@blueship.gr",
        "text": """GOOD DAY,
PLEASED TO HEAR.
MV BLUE STAR (38K DWT) - OPEN 25 MAY GABES, TUNISIA

GEARED SELF-TRIMMING SINGLE DECK BULK CARRIER
BUILT 2011 SAMHO SHIPBUILDING CO LTD, KOREA
LIBERIAN FLAG / CLASSED HIGHEST ABS
37,947 MTDWT ON 10.63M SSW
LOA 179.98 / BEAM 30.00M
GT/NT 23.204/11.900
5 H/H
CARGO HOLDS CUBIC 48,133.5/46,689.5 CBM (GRAIN/BALE)
4 X 35MT CRANES
CO2 FITTED / ELECTRICAL VENTILATED
BWTS FITTED (ALPHA LAVAL)

SPEED AND CONSUMPTION:
ABT 11.0 KN ON ABT 17.0 (L)/ ABT 11.5 ON ABT 16.0 (B) MT IFO
PORT CONSUMPTION: 2.5MT IDLE / 5MT (WORKING CRANES) IFO""",
    },
    {
        "subject": "OPEN TONNAGE ECSA + W.AFRICA + CONTI/MED – 21 MAY 2026",
        "sender": "chartering@haiship.cn",
        "text": """GOOD DAY,
PLS PROPOSE FOR THE BELOW TONNAGE LIST:

ECSA + W. AFRICA
MV DE SHENG HAI DWT 38,821.5 MT OPEN MUCURIPE, BRAZIL O/A 24-25 MAY 2026

CONTI+MED
M/V AN DING HAI DWT 38,800 MT - OPEN CASABLANCA O/A 28-30 MAY 2026

VSL PARTICULAR:
MV AN DING HAI
2017 BLT HONG KONG FLAG SDBC
38800.9 DWT ON 10.5M SSW
GRAIN/BALE CAPACITY 50873.7/49572.6 M3
LOA/BEAM 179.95/32.00M
5 HO/5 HA
GEAR: 4 X 30 TON CRANES, 4 X 10 CBM RADIO REMOTE CONTROL GRAB""",
    },
    {
        "subject": "VC CARGO – KOH SI CHANG TO KANDLA/CHENNAI – MID JULY",
        "sender": "chartering@broker1.com",
        "text": """22 MAY 2026
ATTN CHARTERING DESK!
DEAR SIR
GOOD DAY
PLEASE OFFER FIRM FOR FOLL FULLY FIRM CARGO

15,000 - 20,000 MTS 10PCT MOLOCHOPT
LOAD PORT: KOH SI CHANG, THAILAND
DISCHARGE PORT: KANDLA + CHENNAI
LOAD RATE: 1,000 MTS PWWD SSHEX
DISCHARGE RATE: 1500 MTS PWWD SSHEX
LAYCAN: MID JULY 2026
COM: 3.75 PCT TTL""",
    },
    {
        "subject": "CARGO OFFERS – JEDDAH/BILBAO, IRON SLAG, UREA",
        "sender": "lidomar@lidomar.ro",
        "text": """MCD LIDOMAR
Att. Chartering Desk

Jeddah / Bilbao
20 000 mt HRC max 28,5 mt
FIOS
4000 mt FHINC / CQD disch
25 June - 5 July try later
3.75% here

+++++++++++++++++++++++++++++++++++++++++++++++++

PLS OFFER FIRM FOR FOLL OUR CLOSE AND DIR CHRTRS

20-30,000 mts iron slag in bulk
LP: Bushehr
DP: Doha
10000/12000
25-30 July
3.75% TTL

+++++++++++++++++++++++++++++++++++++++++++++++++

Cargo: 30,000 mts of Urea in bulk
POL: BIK
POD: Iskenderun or Durban
5000/5000
LAYCAN: 16-20 July
COMM: 1.25% TTL""",
    },
    {
        "subject": "TC CARGO REQUIREMENTS – CHINA/NOPAC, SEASIA, WORLDWIDE",
        "sender": "chartering@daian.com",
        "text": """GOOD DAY,
PLEASED TO HEAR.

CHINA / NOPAC
ACC DAI AN OCEAN SHIPPING COMPANY LIMITED
DELIVERY TM VANCOUVER
LC 10-17 JUNE
SMX-UMX, PREF UMX
1 TCT WITH GRAINS
REDELIVERY CHITTAGONG
3.75 ADDCOM PUS

----------------------------------------------

SEASIA
ACC DAI AN OCEAN SHIPPING COMPANY LIMITED
SMX-UMX MAX 20 YRS.
DELY TO MAKE SANGATTA (NEAR TO TJ BARA), E KALI OF INDONESIA.
29-2ND JUN
1 TCT WITH CLINKER TO BDESH.
DURATION ABT 30 DAYS WOG.
3.75PCT ADDOM PUS

----------------------------------------------

WORLDWIDE
ACC DAI AN OCEAN SHIPPING COMPANY LIMITED
SUPRA/ULTRA DELY WW
FULL MAY
1-3 YEARS TRY SHORT PERIOD
FLAT OR INDEX BOTH WORKABLE
3.75 ADDCOM PUS""",
    },
    {
        "subject": "TC REQUIREMENTS – A/C SEA SCHIFFE – ECI DELIVERY",
        "sender": "switson87@seaschiffe.com",
        "text": """Please provide suitable, rated vessels for our following firm requirements.

* A/C SeaSchiffe
* 1 TCT with Steels/Gens/lawfuls
* 22k dwt upto HMAX
* Delivery: ECI
* Laycan: 15-18 July
* Redel: Med via GOA transit
* Duration: abt 35-40 days wog
* 3.75% Adc

----------------------------------------------

* A/C SeaSchiffe
* 1 TCT with Steels/Gens/lawfuls
* 33k dwt upto HMAX
* Delivery: ECI
* Laycan: 21-23 July
* Redel: ARAG via COGH transit
* Duration: abt 50-55 days wog
* 3.75% Adc

We look forward to hearing from you.
Best regards,
Steve
Sea Schiffe DMCC""",
    },
]


def seed():
    session = get_session()
    try:
        count = session.query(Email).count()
        if count > 0:
            print(f"[ShipSeg] Database already has {count} emails. Skipping seed.")
            return

        print("[ShipSeg] Seeding database with sample shipping emails...")
        for sample in SAMPLE_EMAILS:
            text = sample['text']
            category, confidence = classify(text)
            email_obj = Email(
                subject=sample['subject'],
                sender=sample['sender'],
                raw_body=text,
                category=category,
                confidence=confidence,
            )
            session.add(email_obj)
            session.flush()
            extract(category, text, email_obj.id, session)
            print(f"  + [{category.upper():10s}] {sample['subject'][:60]}")

        session.commit()
        print(f"[ShipSeg] Seeded {len(SAMPLE_EMAILS)} emails successfully.")
    except Exception as exc:
        session.rollback()
        print(f"[ShipSeg] Seed error: {exc}")
        raise
    finally:
        session.close()


if __name__ == '__main__':
    seed()
