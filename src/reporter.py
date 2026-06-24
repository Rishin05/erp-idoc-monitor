# src/reporter.py
# Phase 3 — Report Generation
# Writes two outputs:
#   1. A structured JSON log (machine-readable, like what a real system would produce)
#   2. A clean .txt summary (human-readable, like what you'd send to a team lead)

import json
import os
from datetime import datetime


def generate_reports(batch_result, output_dir="output"):
    """
    Takes the output from error_detector.analyze_batch()
    Writes a JSON report and a .txt summary to the output/ folder
    """

    # Make sure output folder exists
    os.makedirs(output_dir, exist_ok=True)

    # Timestamp for filenames — so every run produces a unique report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = os.path.join(output_dir, f"idoc_report_{timestamp}.json")
    txt_path  = os.path.join(output_dir, f"idoc_summary_{timestamp}.txt")

    # --- Output 1: JSON Report ---
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(batch_result, f, indent=2)

    print(f"JSON report saved: {json_path}")

    # --- Output 2: Human-Readable .txt Summary ---
    summary = batch_result["summary"]
    results = batch_result["results"]

    lines = []

    # Header block
    lines.append("=" * 65)
    lines.append("       SAP IDOC ERROR MONITOR — RUN REPORT")
    lines.append(f"       Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 65)
    lines.append("")

    # Batch summary block
    lines.append("BATCH SUMMARY")
    lines.append("-" * 40)
    lines.append(f"  Total IDOCs Processed : {summary['total_idocs']}")
    lines.append(f"  Successful            : {summary['successful']}")
    lines.append(f"  Errors Detected       : {summary['errors']}")
    lines.append(f"  High Severity         : {summary['high_severity']}")
    lines.append(f"  Medium Severity       : {summary['medium_severity']}")
    lines.append("")

    # --- Errors first, sorted by severity ---
    errors  = [r for r in results if r["is_error"]]
    success = [r for r in results if not r["is_error"]]

    # Sort: HIGH before MEDIUM
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "NONE": 3}
    errors.sort(key=lambda r: severity_order.get(r["classification"]["severity"], 99))

    if errors:
        lines.append("FAILED IDOCs")
        lines.append("=" * 65)

        for r in errors:
            c = r["classification"]

            lines.append("")
            lines.append(f"  File          : {r['file']}")
            lines.append(f"  Document #    : {r['doc_number']}")
            lines.append(f"  Message Type  : {r['message_type']}")
            lines.append(f"  Direction     : {r['direction']}")
            lines.append(f"  Sender        : {r['sender']}")
            lines.append(f"  Receiver      : {r['receiver']}")
            lines.append(f"  Status        : {r['status_code']} — {r['status_desc']}")
            lines.append(f"  Severity      : {c['severity']}")
            lines.append(f"  Error Type    : {c['error_type']}")
            lines.append(f"  Likely Cause  : {c['likely_cause']}")
            lines.append(f"  Action        : {c['action']}")

            # Flagged segments
            if r.get("flagged_segments"):
                lines.append(f"  Flagged Segs  :")
                for seg in r["flagged_segments"]:
                    lines.append(f"    [{seg['segment']}] {seg['issue']}")

            lines.append("  " + "-" * 55)

    # --- Successful IDOCs ---
    if success:
        lines.append("")
        lines.append("SUCCESSFUL IDOCs")
        lines.append("=" * 65)

        for r in success:
            lines.append("")
            lines.append(f"  File          : {r['file']}")
            lines.append(f"  Document #    : {r['doc_number']}")
            lines.append(f"  Message Type  : {r['message_type']}")
            lines.append(f"  Direction     : {r['direction']}")
            lines.append(f"  Status        : {r['status_code']} — {r['status_desc']}")
            lines.append(f"  Result        : Processed successfully. No action required.")
            lines.append("  " + "-" * 55)

    lines.append("")
    lines.append("=" * 65)
    lines.append("END OF REPORT")
    lines.append("=" * 65)

    # Write it
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"TXT summary saved:  {txt_path}")

    return json_path, txt_path