# src/error_detector.py
# Phase 2 — Error Detection & Classification
# Takes parsed IDOC data and determines error type, severity, and recommended action

# --- Error Classification Rules ---
# In real SAP environments, each message type fails for predictable reasons
# This maps message type + status code to a human-readable diagnosis

ERROR_RULES = {
    ("ORDERS", "51"): {
        "error_type":  "Application Error — Purchase Order Rejected",
        "likely_cause": "Missing or invalid material number, vendor not found, or price discrepancy",
        "severity":    "HIGH",
        "action":      "Check E1EDP01 segment for material/quantity fields. Correct and reprocess IDOC.",
    },
    ("ORDERS", "56"): {
        "error_type":  "No Inbound Processing — Partner Profile Missing",
        "likely_cause": "Sender partner profile not configured in SAP",
        "severity":    "HIGH",
        "action":      "Verify partner profile in WE20. Add missing inbound parameter for ORDERS.",
    },
    ("INVOIC", "51"): {
        "error_type":  "Application Error — Invoice Posting Failed",
        "likely_cause": "PO reference mismatch, duplicate invoice number, or tax code error",
        "severity":    "HIGH",
        "action":      "Compare invoice against originating PO. Check for duplicate DOCNUM.",
    },
    ("INVOIC", "56"): {
        "error_type":  "No Inbound Processing — Invoice Partner Profile Missing",
        "likely_cause": "Inbound INVOIC process code not assigned to partner",
        "severity":    "MEDIUM",
        "action":      "Check WE20 for partner and assign INVOIC inbound process code.",
    },
    ("DESADV", "51"): {
        "error_type":  "Application Error — Delivery Notification Failed",
        "likely_cause": "Delivery number not found or goods already received",
        "severity":    "MEDIUM",
        "action":      "Verify delivery document exists in SAP. Check if GR already posted.",
    },
    ("DESADV", "56"): {
        "error_type":  "No Processing — Delivery Partner Profile Missing",
        "likely_cause": "WMS system not configured as partner in SAP",
        "severity":    "MEDIUM",
        "action":      "Register WMS partner profile in WE20 for DESADV message type.",
    },
}

# Fallback for any combo we haven't mapped yet
DEFAULT_ERROR = {
    "error_type":  "Unknown Error",
    "likely_cause": "Status code not mapped to a known rule",
    "severity":    "LOW",
    "action":      "Review IDOC manually in SAP transaction WE02 or WE05.",
}


def classify_error(parsed_idoc):
    """
    Takes the output from parser.parse_idoc()
    Returns an enriched dict with error classification or a success note
    """

    header = parsed_idoc["header"]
    message_type = header["message_type"]   # e.g. ORDERS, INVOIC, DESADV
    status_code  = header["status_code"]    # e.g. 51, 56, 03
    is_error     = header["is_error"]

    result = {
        "file":         parsed_idoc["file"],
        "doc_number":   header["doc_number"],
        "message_type": message_type,
        "direction":    header["direction"],
        "sender":       header["sender"],
        "receiver":     header["receiver"],
        "status_code":  status_code,
        "status_desc":  header["status_desc"],
        "is_error":     is_error,
    }

    if not is_error:
        # Clean IDOC — no action needed
        result["classification"] = {
            "error_type":   "None — Successfully Processed",
            "likely_cause": "N/A",
            "severity":     "NONE",
            "action":       "No action required.",
        }
        return result

    # Look up the rule for this message type + status combo
    rule_key = (message_type, status_code)
    classification = ERROR_RULES.get(rule_key, DEFAULT_ERROR)

    result["classification"] = classification

    # --- Segment-level analysis ---
    # Flag any data segments that have suspiciously few fields
    # In real SAP, incomplete segments are a common root cause
    flagged_segments = []
    for seg in parsed_idoc["segments"]:
        field_count = len(seg["fields"])
        if field_count == 0:
            flagged_segments.append({
                "segment": seg["segment_name"],
                "issue":   "Empty segment — no fields populated",
            })
        elif field_count < 2:
            flagged_segments.append({
                "segment": seg["segment_name"],
                "issue":   f"Sparse segment — only {field_count} field(s) found, possible missing data",
            })

    result["flagged_segments"] = flagged_segments

    return result


def analyze_batch(parsed_idocs):
    """
    Runs classify_error on a list of parsed IDOCs
    Returns classified results + a summary
    """

    results = [classify_error(idoc) for idoc in parsed_idocs]

    # Build a quick summary
    total       = len(results)
    errors      = [r for r in results if r["is_error"]]
    successes   = [r for r in results if not r["is_error"]]
    high        = [r for r in errors if r["classification"]["severity"] == "HIGH"]
    medium      = [r for r in errors if r["classification"]["severity"] == "MEDIUM"]

    summary = {
        "total_idocs":    total,
        "successful":     len(successes),
        "errors":         len(errors),
        "high_severity":  len(high),
        "medium_severity": len(medium),
    }

    return {
        "summary": summary,
        "results": results,
    }