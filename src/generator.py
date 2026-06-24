# src/generator.py
# Generates realistic bulk IDOC XML files for stress testing
# Simulates a production SAP environment with mixed statuses and message types

import os
import random
from lxml import etree

# --- Configuration ---
# Weighted so ~70% success, ~30% errors (realistic production ratio)
STATUS_WEIGHTS = {
    "03": 60,   # Success
    "51": 25,   # Application Error (most common failure)
    "56": 10,   # No inbound processing
    "68": 5,    # No further processing
}

MESSAGE_TYPES = {
    "ORDERS":  "ORDERS05",    # Purchase Orders
    "INVOIC":  "INVOIC02",    # Invoices
    "DESADV":  "DELVRY03",    # Delivery Notifications
    "HRMD":    "HRMD_A08",    # HR Master Data
    "MATMAS":  "MATMAS05",    # Material Master
}

VENDORS = [
    "VENDOR_01", "VENDOR_02", "VENDOR_03", "VENDOR_04",
    "VENDOR_05", "SUPPLIER_CA", "SUPPLIER_US", "PARTNER_EU",
]

RECEIVERS = [
    "SAP_PROD", "SAP_QAS", "WMS_01", "ERP_CORE", "HR_SYSTEM", "MDM_HUB"
]

CURRENCIES = ["CAD", "USD", "EUR", "GBP"]
UNITS      = ["EA", "KG", "LB", "PC", "BOX"]


def weighted_choice(weight_dict):
    """Pick a key from a dict based on weighted values"""
    keys    = list(weight_dict.keys())
    weights = list(weight_dict.values())
    return random.choices(keys, weights=weights, k=1)[0]


def build_segment_data(message_type):
    """
    Returns a list of (segment_name, fields_dict) tuples
    based on the message type — mimics real SAP segment structures
    """
    segments = []

    if message_type == "ORDERS":
        segments.append(("E1EDK01", {
            "ACTION": "000",
            "CURCY":  random.choice(CURRENCIES),
            "WKURS":  str(round(random.uniform(0.75, 1.35), 4)),
            "BSART":  random.choice(["NB", "ZNB", "ZORD"]),
        }))
        # Add 1-3 line items
        for i in range(1, random.randint(2, 4)):
            segments.append((f"E1EDP01", {
                "POSEX": str(i * 10).zfill(6),
                "MENGE": str(random.randint(1, 500)),
                "MENEE": random.choice(UNITS),
                "NETPR": str(round(random.uniform(5.0, 999.99), 2)),
            }))

    elif message_type == "INVOIC":
        segments.append(("E1EDKA1", {
            "PARVW": "RE",
            "PARTN": random.choice(VENDORS),
        }))
        segments.append(("E1EDK01", {
            "CURCY": random.choice(CURRENCIES),
            "BELNR": str(random.randint(1000000, 9999999)),
        }))
        for i in range(1, random.randint(2, 5)):
            segments.append(("E1EDP01", {
                "POSEX": str(i * 10).zfill(6),
                "MENGE": str(random.randint(1, 200)),
                "MENEE": random.choice(UNITS),
                "VPREI": str(round(random.uniform(10.0, 500.0), 2)),
            }))

    elif message_type == "DESADV":
        segments.append(("E1EDL20", {
            "VBELN": str(random.randint(80000000, 89999999)),
            "VSTEL": str(random.randint(1000, 9999)),
            "LGNUM": str(random.randint(100, 999)),
        }))
        segments.append(("E1EDL24", {
            "VBELN": str(random.randint(80000000, 89999999)),
            "POSNR": "000010",
            "MATNR": f"MAT{random.randint(10000, 99999)}",
            "LFIMG": str(random.randint(1, 300)),
        }))

    elif message_type == "HRMD":
        segments.append(("E1PLOGI", {
            "PERNR": str(random.randint(10000000, 99999999)),
            "BEGDA": "20240101",
            "ENDDA": "99991231",
        }))
        segments.append(("E1P0001", {
            "BUKRS": str(random.randint(1000, 9999)),
            "WERKS": str(random.randint(1000, 9999)),
            "KOSTL": str(random.randint(1000000, 9999999)),
        }))

    elif message_type == "MATMAS":
        segments.append(("E1MARAM", {
            "MATNR": f"MAT{random.randint(10000, 99999)}",
            "MTART": random.choice(["FERT", "ROH", "HALB", "HIBE"]),
            "MEINS": random.choice(UNITS),
            "MATKL": f"{random.randint(10, 99)}",
        }))
        segments.append(("E1MAKTM", {
            "SPRAS": "EN",
            "MAKTX": f"Material Description {random.randint(100, 999)}",
        }))

    return segments


def generate_idoc(doc_number, output_dir):
    """Generates a single IDOC XML file"""

    message_type = random.choice(list(MESSAGE_TYPES.keys()))
    idoc_type    = MESSAGE_TYPES[message_type]
    status       = weighted_choice(STATUS_WEIGHTS)
    direction    = random.choice(["1", "2"])  # 1=Outbound, 2=Inbound
    sender       = random.choice(VENDORS)
    receiver     = random.choice(RECEIVERS)

    # Build XML tree
    root = etree.Element("IDOC", BEGIN="1")

    # Control Record
    ctrl = etree.SubElement(root, "EDI_DC40", SEGMENT="1")
    fields = {
        "TABNAM":  "EDI_DC40",
        "MANDT":   "100",
        "DOCNUM":  str(doc_number).zfill(16),
        "DIRECT":  direction,
        "IDOCTYP": idoc_type,
        "MESTYP":  message_type,
        "SNDPRT":  "LS",
        "SNDPRN":  sender,
        "RCVPRT":  "LS",
        "RCVPRN":  receiver,
        "STATUS":  status,
    }
    for tag, val in fields.items():
        el = etree.SubElement(ctrl, tag)
        el.text = val

    # Data Segments
    for seg_name, seg_fields in build_segment_data(message_type):
        seg_el = etree.SubElement(root, seg_name, SEGMENT="1")
        for tag, val in seg_fields.items():
            el = etree.SubElement(seg_el, tag)
            el.text = str(val)

    # Write to file
    tree     = etree.ElementTree(root)
    filename = f"idoc_{str(doc_number).zfill(5)}.xml"
    filepath = os.path.join(output_dir, filename)

    tree.write(filepath, pretty_print=True,
               xml_declaration=True, encoding="UTF-8")

    return filename


def generate_batch(count=100, output_dir="sample_idocs"):
    """Generate a batch of IDOC XML files"""
    os.makedirs(output_dir, exist_ok=True)

    # Clear old files first
    for f in os.listdir(output_dir):
        if f.endswith(".xml"):
            os.remove(os.path.join(output_dir, f))

    print(f"Generating {count} IDOC files into '{output_dir}/'...\n")

    for i in range(1, count + 1):
        doc_number = 1000000000000 + i
        generate_idoc(doc_number, output_dir)
        if i % 10 == 0:
            print(f"  {i}/{count} generated...")

    print(f"\nDone. {count} IDOC files ready.\n")