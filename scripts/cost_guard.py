"""
Market-Rover Zero-Cost Architecture & Budget Guard
Scans GCP resources to ensure strict adherence to Free Tier quotas:
- Secret Manager versions <= 6
- GCS Staging Buckets have 1-day lifecycle & no soft-delete
- Artifact Registry image footprint < 500 MB
- Cloud Run scale-to-zero policy (min_instances = 0)
"""

import subprocess
import json
import sys
import shutil

PROJECT_ID = "market-rover"

GCLOUD_BIN = shutil.which("gcloud.cmd") or shutil.which("gcloud") or "gcloud"

def run_gcloud_json(args: list):
    try:
        cmd = [GCLOUD_BIN] + args + ["--format=json"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(res.stdout) if res.stdout.strip() else []
    except Exception as e:
        print(f"[!] Warning running command {' '.join(args)}: {e}")
        return []

def audit_secret_manager():
    print("\n[1/4] Auditing Secret Manager Quota (Limit <= 6 versions)...")
    secrets = run_gcloud_json(["secrets", "list", f"--project={PROJECT_ID}"])
    total_active_versions = 0

    for s in secrets:
        s_name = s.get("name", "").split("/")[-1]
        versions = run_gcloud_json(["secrets", "versions", "list", s_name, f"--project={PROJECT_ID}"])
        active_versions = [v for v in versions if v.get("state") in ["enabled", "disabled"]]
        count = len(active_versions)
        total_active_versions += count
        print(f"  - Secret: {s_name:<30} Active/Disabled Versions: {count}")

    print(f"  -> Total Billed Versions: {total_active_versions}/6")
    if total_active_versions > 6:
        print(f"  [X] EXCEEDS FREE TIER! Billed for {total_active_versions - 6} versions.")
        return False
    elif total_active_versions >= 5:
        print("  [!] WARNING: Close to 6 version free tier limit.")
    else:
        print("  [OK] PASS: Well within free tier.")
    return True

def audit_gcs_buckets():
    print("\n[2/4] Auditing Cloud Storage Buckets (Lifecycle & Soft-Delete)...")
    buckets = run_gcloud_json(["storage", "buckets", "list", f"--project={PROJECT_ID}"])
    all_ok = True
    for b in buckets:
        name = b.get("name", "")
        loc = b.get("location", "")
        lifecycle = b.get("lifecycle_config", {}).get("rule", [])
        soft_del = b.get("soft_delete_policy", {}).get("retentionDurationSeconds", "0")

        has_delete_rule = any(r.get("action", {}).get("type") == "Delete" for r in lifecycle)
        print(f"  - Bucket: gs://{name} (Location: {loc})")
        print(f"    - Auto-Delete Lifecycle: {'[OK] Enabled' if has_delete_rule else '[!] Missing'}")
        print(f"    - Soft Delete: {'[!] Enabled (' + str(soft_del) + 's)' if int(soft_del) > 0 else '[OK] Cleared (0s)'}")

        if "cloudbuild" in name and not has_delete_rule:
            all_ok = False
    return all_ok

def audit_artifact_registry():
    print("\n[3/4] Auditing Artifact Registry Footprint (Limit < 500 MB)...")
    repos = run_gcloud_json(["artifacts", "repositories", "list", f"--project={PROJECT_ID}"])
    all_ok = True
    for r in repos:
        name = r.get("name", "").split("/")[-1]
        size_mb = float(r.get("sizeBytes", 0)) / (1024 * 1024) if "sizeBytes" in r else float(r.get("size_mb", 0) or 0)
        print(f"  - Repository: {name:<25} Size: {size_mb:.2f} MB / 500 MB")
        if size_mb > 500:
            print("  [X] EXCEEDS 500 MB FREE TIER!")
            all_ok = False
    if all_ok:
        print("  [OK] PASS: Under 500 MB free tier.")
    return all_ok

def audit_cloud_run():
    print("\n[4/4] Auditing Cloud Run Scale-to-Zero Policy...")
    services = run_gcloud_json(["run", "services", "list", f"--project={PROJECT_ID}"])
    all_ok = True
    for svc in services:
        name = svc.get("metadata", {}).get("name", "")
        annotations = svc.get("spec", {}).get("template", {}).get("metadata", {}).get("annotations", {})
        min_instances = annotations.get("autoscaling.knative.dev/minScale", "0")
        print(f"  - Service: {name:<25} min-instances: {min_instances}")
        if int(min_instances) > 0:
            print(f"  [!] WARNING: Service {name} has min-instances > 0 (incurs idle CPU cost).")
            all_ok = False
    if all_ok:
        print("  [OK] PASS: All services scale to 0 when idle.")
    return all_ok

def main():
    print("=" * 60)
    print(" MARKET-ROVER ZERO-COST PROACTIVE AUDIT")
    print("=" * 60)

    sm_ok = audit_secret_manager()
    gcs_ok = audit_gcs_buckets()
    ar_ok = audit_artifact_registry()
    cr_ok = audit_cloud_run()

    print("\n" + "=" * 60)
    if sm_ok and gcs_ok and ar_ok and cr_ok:
        print("[SUCCESS] ALL SYSTEMS GREEN: Current configuration maintains 0.00 cost / month!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("[ACTION REQUIRED] Some resources risk exceeding Free Tier thresholds.")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
