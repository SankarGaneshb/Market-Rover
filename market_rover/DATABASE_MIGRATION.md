# Database Migration & Cloud SQL Decommissioning Report

**Date of Decommissioning:** August 11, 2026
**Project:** Market-Rover & InvestBrand
**GCP Project ID:** `market-rover` (Number: `9514347926`)

---

## 1. Migration Overview

To optimize operational costs and simplify database management, the PostgreSQL backend has transitioned from Google Cloud SQL to a serverless **Neon PostgreSQL** database.

* **Active Database:** Neon PostgreSQL (Shared Database)
* **Connection DSN:** `postgresql://neondb_owner:***@ep-polished-credit-axjx44dk.c-4.us-east-2.aws.neon.tech/neondb?sslmode=require`
* **Affected Cloud Run Services:**
  - `investbrand-api` (Updated to `investbrand-api-00122-z8f` or later)
  - `market-rover-api` (Updated to `market-rover-api-00043-9kc` or later)
* **GCP Cloud SQL Decommissioned:** `investcraft-db` (Deleted successfully on 2026-08-11)

---

## 2. Pre-Deletion Backups (Cloud Storage)

Before deleting the Cloud SQL instance, the databases were fully backed up using `gcloud sql export sql` to prevent any data loss. The backups are stored as static SQL dump files in Google Cloud Storage.

* **Backup Bucket:** `gs://market-rover_cloudbuild/sql-backups/`
* **GCS Console Path:** [market-rover_cloudbuild/sql-backups/](https://console.cloud.google.com/storage/browser/market-rover_cloudbuild/sql-backups;tab=objects?project=market-rover)

### Backup Archive Inventory:
1. **`postgres_backup.sql`**: Main database backup containing schema, configuration, and data for the `postgres` database (shared by InvestBrand).
2. **`market_rover_backup.sql`**: Historical database dump for the `market_rover` database (Legacy/Obsolete).
3. **`hil_rover_backup.sql`**: Historical database dump for the `hil_rover` database (Legacy/Obsolete).
4. **`pledgerover_backup.sql`**: Historical database dump for the `pledgerover` database (Legacy/Obsolete).

---

## 3. Restoring from Backup (Reference Guide)

In the event that historical data from the old Cloud SQL instance needs to be queried or restored:

### Local Restore:
To import any backup SQL file into a local PostgreSQL database:
```bash
# 1. Download the backup file from Cloud Storage
gcloud storage cp gs://market-rover_cloudbuild/sql-backups/postgres_backup.sql .

# 2. Import into your local PostgreSQL instance
psql -h localhost -U postgres -d postgres -f postgres_backup.sql
```

### Neon Restore (or new Cloud SQL):
To import the dump into a remote instance:
```bash
psql "postgresql://user:password@host/dbname?sslmode=require" -f postgres_backup.sql
```

---

## 4. Decommissioning Log

1. **Verify Services:** Confirmed both local development server and Cloud Run production backend successfully connect, run migrations, and write data to the Neon DB.
2. **IAM Authorization:** Added storage permission (`roles/storage.objectAdmin`) to Cloud SQL service account (`p9514347926-exr4jf@gcp-sa-cloud-sql.iam.gserviceaccount.com`) on the bucket `gs://market-rover_cloudbuild/`.
3. **DB Export:** Ran individual exports for `postgres`, `market_rover`, `hil_rover`, and `pledgerover` databases to GCS.
4. **Deletion:** Deleted the `investcraft-db` instance via `gcloud sql instances delete investcraft-db --quiet`. All active daily database host charges have ceased.
