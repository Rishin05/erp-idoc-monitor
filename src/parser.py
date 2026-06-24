# src/parser.py
# Reads an IDOC XML file and extracts header info + all segments

from lxml import etree
import os


STATUS_CODES = {
    "03": "Passed to Application",       
    "51": "Application Error",          
    "56": "IDOC with Errors Added",      
    "68": "Error — No Further Processing",
    "02": "Error Passing Data to Port",  
}

def parse_idoc(filepath):
    """
    Parses a single IDOC XML file.
    Returns a dictionary with header fields and all segments.
    """

    # Check the file actually exists before trying to open it
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"IDOC file not found: {filepath}")

    # lxml parses the XML file into a tree structure
    tree = etree.parse(filepath)
    root = tree.getroot()  # This is the <IDOC> root element

    # --- Extract the Control Record (EDI_DC40) ---
    # EDI_DC40 is always the first segment — it's the IDOC header/envelope
    control = root.find("EDI_DC40")

    if control is None:
        raise ValueError(f"No EDI_DC40 control record found in {filepath}")

    # Pull the key fields we care about from the header
    def get(field):
        """Helper — safely gets text from a child element"""
        el = control.find(field)
        return el.text.strip() if el is not None and el.text else "N/A"

    status_code = get("STATUS")

    header = {
        "doc_number":   get("DOCNUM"),    # Unique IDOC number
        "idoc_type":    get("IDOCTYP"),   # e.g. ORDERS05, INVOIC02
        "message_type": get("MESTYP"),    # e.g. ORDERS, INVOIC, DESADV
        "direction":    "Inbound" if get("DIRECT") == "2" else "Outbound",
        "sender":       get("SNDPRN"),    # Who sent it
        "receiver":     get("RCVPRN"),    # Who receives it
        "status_code":  status_code,
        "status_desc":  STATUS_CODES.get(status_code, "Unknown Status"),
        "is_error":     status_code not in ["03"],  # 03 is the only clean success
    }

    # --- Extract all data segments ---
    # Everything that isn't EDI_DC40 is a data segment
    segments = []
    for element in root:
        if element.tag == "EDI_DC40":
            continue  # skip the header, we already handled it

        segment_data = {}
        for child in element:
            if child.text and child.text.strip():
                segment_data[child.tag] = child.text.strip()

        segments.append({
            "segment_name": element.tag,
            "fields": segment_data
        })

    return {
        "file": os.path.basename(filepath),
        "header": header,
        "segments": segments
    }