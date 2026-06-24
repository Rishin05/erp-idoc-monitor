# main.py
import os
import argparse
from src.generator import generate_batch
from src.parser import parse_idoc
from src.error_detector import analyze_batch
from src.reporter import generate_reports

# --- Argument: how many IDOCs to generate ---
# Run as: python main.py --count 100
# Defaults to 50 if no argument given

parser = argparse.ArgumentParser(description="SAP IDOC Error Monitor")
parser.add_argument("--count", type=int, default=50,
                    help="Number of IDOCs to generate (default: 50)")
parser.add_argument("--skip-gen", action="store_true",
                    help="Skip generation, use existing files in sample_idocs/")
args = parser.parse_args()

idoc_folder = "sample_idocs"

# --- Step 1: Generate ---
if not args.skip_gen:
    generate_batch(count=args.count, output_dir=idoc_folder)

# --- Step 2: Parse ---
parsed = []
files  = sorted([f for f in os.listdir(idoc_folder) if f.endswith(".xml")])

print(f"Parsing {len(files)} IDOC files...")
for filename in files:
    filepath = os.path.join(idoc_folder, filename)
    parsed.append(parse_idoc(filepath))

print(f"Parsed {len(parsed)} IDOCs successfully\n")

# --- Step 3: Detect errors ---
batch_result = analyze_batch(parsed)

# --- Step 4: Report ---
print("Generating reports...\n")
generate_reports(batch_result)

# --- Step 5: Print console summary ---
s = batch_result["summary"]
print("\n========= FINAL SUMMARY =========")
print(f"  Total Processed  : {s['total_idocs']}")
print(f"  Successful       : {s['successful']}")
print(f"  Errors           : {s['errors']}")
print(f"  High Severity    : {s['high_severity']}")
print(f"  Medium Severity  : {s['medium_severity']}")
print("==================================")
print("\nFull reports saved to output/")