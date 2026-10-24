import os
import sys
import json
import asyncio
import argparse

# Add project root to sys.path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.services.extraction.pipeline import extract_invoice

FIELDS_TO_EVALUATE = [
    ("supplier_name", "Supplier Name", "str"),
    ("gstin", "Supplier GSTIN", "str"),
    ("buyer_gstin", "Buyer GSTIN", "str"),
    ("invoice_number", "Invoice Number", "str"),
    ("invoice_date", "Invoice Date", "str"),
    ("total_amount", "Total Gross Amount", "num"),
    ("taxable_amount", "Taxable Base", "num"),
    ("cgst", "CGST Amount", "num"),
    ("sgst", "SGST Amount", "num"),
    ("igst", "IGST Amount", "num"),
]

def normalize_str(s):
    if not s:
        return ""
    import re
    return re.sub(r"[^\w]", "", str(s)).lower()

async def evaluate_corpus(folder_path: str):
    if not os.path.isdir(folder_path):
        print(f"Directory '{folder_path}' does not exist.")
        sys.exit(1)

    pdf_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")])
    if not pdf_files:
        print(f"No PDF files found in '{folder_path}'.")
        sys.exit(1)

    eval_pairs = []
    for pdf in pdf_files:
        base_name = os.path.splitext(pdf)[0]
        json_file = f"{base_name}.expected.json"
        json_path = os.path.join(folder_path, json_file)
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f_j:
                eval_pairs.append((os.path.join(folder_path, pdf), json.load(f_j)))

    print(f"\n================================================================================")
    print(f" VendorShield AI — Layered Extraction Benchmark Evaluation")
    print(f" Target Folder: {folder_path} ({len(eval_pairs)} benchmark test pairs)")
    print(f"================================================================================\n")

    stats = {field: {"total": 0, "correct": 0, "sources": {}} for field, _, _ in FIELDS_TO_EVALUATE}

    for pdf_path, expected in eval_pairs:
        with open(pdf_path, "rb") as f_pdf:
            content = f_pdf.read()

        filename = os.path.basename(pdf_path)
        extracted = await extract_invoice(content, filename=filename)

        print(f"Evaluated: {filename:<32} | Total: INR {extracted.total_amount:<10,.2f} | GSTIN: {extracted.gstin or 'MISSING':<15}")

        for field, label, ftype in FIELDS_TO_EVALUATE:
            exp_val = expected.get(field)
            act_val = getattr(extracted, field, None)
            meta = extracted.extraction_metadata.get(field)
            source_tag = meta.status.value if meta else "NONE"

            # Record source distribution
            stats[field]["sources"][source_tag] = stats[field]["sources"].get(source_tag, 0) + 1

            if exp_val is None and not act_val:
                stats[field]["total"] += 1
                stats[field]["correct"] += 1
                continue

            if exp_val is not None:
                stats[field]["total"] += 1
                if ftype == "num":
                    # Numerical tolerance within 1.5 INR
                    if act_val is not None and abs(float(act_val) - float(exp_val)) <= 1.5:
                        stats[field]["correct"] += 1
                else:
                    norm_exp = normalize_str(exp_val)
                    norm_act = normalize_str(act_val)
                    if norm_exp in norm_act or norm_act in norm_exp or norm_exp == norm_act:
                        stats[field]["correct"] += 1

    print("\n--------------------------------------------------------------------------------")
    print(f" {'Field Name':<24} | {'Evaluated':<10} | {'Matched':<10} | {'Accuracy %':<12} | Top Sources")
    print("--------------------------------------------------------------------------------")

    total_fields = 0
    total_correct = 0

    for field, label, _ in FIELDS_TO_EVALUATE:
        t = stats[field]["total"]
        c = stats[field]["correct"]
        acc = (c / t * 100.0) if t > 0 else 0.0
        src_str = ", ".join(f"{k}:{v}" for k, v in sorted(stats[field]["sources"].items()))
        print(f" {label:<24} | {t:<10} | {c:<10} | {acc:>8.1f}%   | {src_str}")
        total_fields += t
        total_correct += c

    overall_acc = (total_correct / total_fields * 100.0) if total_fields > 0 else 0.0
    print("--------------------------------------------------------------------------------")
    print(f" OVERALL FIELD ACCURACY : {overall_acc:.1f}% ({total_correct}/{total_fields} evaluated field facts)")
    print("================================================================================\n")
    print("Note for Mentors & AP Leads:")
    print("Drop 10–20 real redacted vendor invoice PDFs with matching .expected.json")
    print("into this folder to evaluate precision on company-specific invoice formats.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate extraction pipeline accuracy over benchmark corpus.")
    parser.add_argument("folder", nargs="?", default="data/sample_invoices", help="Folder containing PDFs and .expected.json files")
    args = parser.parse_args()
    asyncio.run(evaluate_corpus(args.folder))
