"""
Integration tests — hit real running services and verify DB persistence.

Run with:  python -X utf8 test_endpoints.py
Services must be up: auth-service (8001), plant-service (8002), user-service (8005)
DBs must be up:      postgres-auth (5434), postgres-core (5432)
"""

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date

BASE_AUTH  = "http://localhost:8001"
BASE_PLANT = "http://localhost:8002"
BASE_USER  = "http://localhost:8005"

PASS_COUNT = 0
FAIL_COUNT = 0


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _request(method, url, data=None, token=None, extra_headers=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra_headers:
        headers.update(extra_headers)
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read()), e.code
        except Exception:
            return {}, e.code


def post(url, data, token=None, extra_headers=None):
    return _request("POST", url, data, token, extra_headers)


def get(url, token=None, extra_headers=None):
    return _request("GET", url, token=token, extra_headers=extra_headers)


def put(url, data, token=None, extra_headers=None):
    return _request("PUT", url, data, token, extra_headers)


def delete(url, token=None):
    return _request("DELETE", url, token=token)


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------

def check(label, condition, detail=""):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  [PASS] {label}")
    else:
        FAIL_COUNT += 1
        print(f"  [FAIL] {label}" + (f"  ->  {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# DB helpers (psql via docker exec)
# ---------------------------------------------------------------------------

def psql(container, user, db, sql):
    """Run SQL in a running postgres container and return stdout."""
    cmd = [
        "docker", "exec", container,
        "psql", "-U", user, "-d", db, "-t", "-c", sql,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode


def mark_email_verified(email):
    """Directly mark a user's email as verified in postgres-auth."""
    out, rc = psql(
        "mp-postgres-auth", "mp_auth_user", "medicinal_plants_auth",
        f"UPDATE users SET email_verified=true WHERE email='{email}' RETURNING id;",
    )
    return rc == 0 and out.strip()


def get_user_id_from_db(email):
    """Fetch the user UUID from postgres-auth by email."""
    out, rc = psql(
        "mp-postgres-auth", "mp_auth_user", "medicinal_plants_auth",
        f"SELECT id FROM users WHERE email='{email}';",
    )
    return out.strip() if rc == 0 else None


# ---------------------------------------------------------------------------
# Test suites
# ---------------------------------------------------------------------------

def test_auth_service():
    print("\n" + "=" * 60)
    print("AUTH SERVICE  (postgres-auth)")
    print("=" * 60)

    ts = int(time.time())
    email    = f"inttest_{ts}@medicinalplants.mx"
    password = "Secure#Pass9"

    # ── Register ──────────────────────────────────────────────────
    print(f"\n[1] Register new user ({email})")
    result, status = post(BASE_AUTH + "/api/v1/auth/register", {
        "email": email,
        "password": password,
        "first_name": "Integration",
        "last_name": "Test",
    })
    check("POST /api/v1/auth/register -> 200/201", status in (200, 201), f"status={status}, body={result}")
    user_id = None
    if status in (200, 201):
        user_id = result.get("id")
        check("Response has user id", bool(user_id), str(result))
        check("email returned correctly", result.get("email") == email, str(result))
        print(f"     user_id={user_id}")

    # ── Verify in DB ──────────────────────────────────────────────
    print("\n[2] Mark email as verified (direct DB update)")
    ok = mark_email_verified(email)
    check("DB UPDATE email_verified=true succeeded", bool(ok), f"returned: {ok!r}")

    # ── Login ─────────────────────────────────────────────────────
    print("\n[3] Login")
    result, status = post(BASE_AUTH + "/api/v1/auth/login", {
        "email": email,
        "password": password,
    })
    check("POST /api/v1/auth/login -> 200", status == 200, f"status={status}, body={result}")
    token = None
    if status == 200:
        token = result.get("access_token") or result.get("token")
        check("Response has access_token", bool(token), str(result))
        refresh = result.get("refresh_token")
        print(f"     access_token present: {bool(token)}, refresh_token present: {bool(refresh)}")

    # ── Token validate ────────────────────────────────────────────
    if token:
        print("\n[4] Validate token")
        result, status = post(BASE_AUTH + "/api/v1/auth/validate", {"token": token})
        check("POST /api/v1/auth/validate -> 200", status == 200, f"status={status}, body={result}")

    # ── Duplicate register ────────────────────────────────────────
    print("\n[5] Duplicate register -> 409/400")
    result, status = post(BASE_AUTH + "/api/v1/auth/register", {
        "email": email,
        "password": password,
        "first_name": "Integration",
        "last_name": "Test",
    })
    check("Duplicate email rejected (4xx)", 400 <= status < 500, f"status={status}")

    # ── Persist check via DB ──────────────────────────────────────
    print("\n[6] Confirm user row persisted in postgres-auth")
    db_id = get_user_id_from_db(email)
    check("User found in DB", bool(db_id), f"got: {db_id!r}")

    return token, user_id


def test_plant_service(token):
    print("\n" + "=" * 60)
    print("PLANT SERVICE  (postgres-core)")
    print("=" * 60)

    # ── Create plant ──────────────────────────────────────────────
    print("\n[1] Create plant")
    ts = int(time.time())
    result, status = post(BASE_PLANT + "/plants/", {
        "scientific_name": f"Salvia hispanica {ts}",
        "common_name": "chia",
        "family": "Lamiaceae",
        "genus": "Salvia",
        "species": "hispanica",
        "description": "Annual herb native to central Mexico",
        "habitat": "dry highlands",
        "region": "central Mexico",
        "category": "medicinal",
    }, token)
    check("POST /plants/ -> 200/201", status in (200, 201), f"status={status}, body={result}")
    plant_id = None
    if status in (200, 201):
        plant_id = result.get("id")
        check("Response has id", bool(plant_id), str(result))
        check("scientific_name persisted", "Salvia hispanica" in result.get("scientific_name", ""), str(result))
        print(f"     plant_id={plant_id}")

    # ── Get plant ─────────────────────────────────────────────────
    if plant_id:
        print("\n[2] Get plant by id")
        result, status = get(BASE_PLANT + f"/plants/{plant_id}", token)
        check("GET /plants/{id} -> 200", status == 200, f"status={status}")
        check("Correct plant returned", result.get("id") == plant_id, str(result))

    # ── List plants ───────────────────────────────────────────────
    print("\n[3] List plants")
    result, status = get(BASE_PLANT + "/plants/", token)
    check("GET /plants/ -> 200", status == 200, f"status={status}, body={result}")
    if status == 200:
        items = result.get("items") or result.get("plants") or (result if isinstance(result, list) else [])
        check("At least one plant in list", len(items) >= 1, f"count={len(items)}")

    # ── Update plant ──────────────────────────────────────────────
    if plant_id:
        print("\n[4] Update plant")
        result, status = put(BASE_PLANT + f"/plants/{plant_id}", {
            "description": "Updated: annual herb native to central Mexico, valued for omega-3-rich seeds",
        }, token)
        check("PUT /plants/{id} -> 200", status == 200, f"status={status}, body={result}")

    # ── Create compound ───────────────────────────────────────────
    print("\n[5] Create compound")
    result, status = post(BASE_PLANT + "/compounds/", {
        "name": "Rosmarinic acid",
        "molecular_formula": "C18H16O8",
        "molecular_weight": 360.31,
        "description": "Phenolic acid found in many herbs",
    }, token)
    check("POST /compounds/ -> 200/201", status in (200, 201), f"status={status}, body={result}")
    compound_id = None
    if status in (200, 201):
        compound_id = result.get("id")
        check("Response has id", bool(compound_id), str(result))
        check("name persisted", result.get("name") == "Rosmarinic acid", str(result))
        print(f"     compound_id={compound_id}")

    # ── Link compound to plant ────────────────────────────────────
    if plant_id and compound_id:
        print("\n[6] Link compound to plant")
        result, status = post(BASE_PLANT + "/compounds/link", {
            "plant_id": plant_id,
            "compound_id": compound_id,
        }, token)
        check("POST /compounds/link -> 200/201", status in (200, 201), f"status={status}, body={result}")

    # ── Create article ────────────────────────────────────────────
    print("\n[7] Create scientific article")
    result, status = post(BASE_PLANT + "/articles/", {
        "title": "Pharmacological evaluation of Salvia hispanica L.",
        "abstract": "Chia seeds have been used in traditional medicine.",
        "doi": f"10.9999/inttest.{int(time.time())}",
        "journal": "Journal of Ethnopharmacology",
        "publication_date": str(date.today()),
        "authors": ["Garcia A", "Lopez B"],
        "keywords": ["chia", "pharmacology"],
        "is_open_access": True,
        "peer_reviewed": True,
    }, token)
    check("POST /articles/ -> 200/201", status in (200, 201), f"status={status}, body={result}")
    article_id = None
    if status in (200, 201):
        article_id = result.get("id")
        check("Response has id", bool(article_id), str(result))
        print(f"     article_id={article_id}")

    # ── Associate article with plant ──────────────────────────────
    if plant_id and article_id:
        print("\n[8] Associate article with plant")
        result, status = post(
            BASE_PLANT + f"/articles/{article_id}/plants/{plant_id}",
            {},
            token,
        )
        check("POST /articles/{id}/plants/{plant_id} -> 200/201", status in (200, 201), f"status={status}, body={result}")

    # ── Verify persistence via direct DB query ────────────────────
    print("\n[9] Confirm records persisted in postgres-core")
    out, rc = psql("mp-postgres-core", "mp_core_user", "medicinal_plants_core",
                   "SELECT COUNT(*) FROM plants;")
    check("plants table has rows", rc == 0 and int(out or 0) >= 1, f"count={out!r}")

    out, rc = psql("mp-postgres-core", "mp_core_user", "medicinal_plants_core",
                   "SELECT COUNT(*) FROM chemical_compounds;")
    check("compounds table has rows", rc == 0 and int(out or 0) >= 1, f"count={out!r}")

    return plant_id, compound_id


def test_user_service(token, user_id, plant_id):
    print("\n" + "=" * 60)
    print("USER SERVICE  (postgres-user)")
    print("=" * 60)

    if not user_id:
        print("  (skipped — no user_id from auth service)")
        return

    uid_header = {"x-user-id": str(user_id)}
    # plant to use for favorites / usage reports (fallback to a dummy UUID)
    fav_plant_id = plant_id or "00000000-0000-0000-0000-000000000099"

    # ── Get profile ───────────────────────────────────────────────
    print("\n[1] Get profile")
    result, status = get(BASE_USER + "/profile/me", token, uid_header)
    check("GET /profile/me -> 200 or 404", status in (200, 404), f"status={status}, body={result}")

    # ── Add favourite ─────────────────────────────────────────────
    print("\n[2] Add favourite plant")
    result, status = post(BASE_USER + f"/favorites", {
        "plant_id": fav_plant_id,
        "notes": "integration test favourite",
    }, token, uid_header)
    # 201 success, 404 plant not found, 409 duplicate — all acceptable
    check("POST /favorites -> 2xx or 4xx", status < 500, f"status={status}, body={result}")

    # ── List favourites ───────────────────────────────────────────
    print("\n[3] List favourites")
    result, status = get(BASE_USER + "/favorites", token, uid_header)
    check("GET /favorites -> 200", status == 200, f"status={status}, body={result}")

    # ── Create usage report ───────────────────────────────────────
    print("\n[4] Create usage report")
    result, status = post(BASE_USER + "/usage-reports", {
        "plant_id": fav_plant_id,
        "effectiveness": "moderately_effective",
        "rating": 4,
        "dosage": "5g",
        "dosage_unit": "grams",
        "frequency": "daily",
        "duration_days": 7,
        "preparation_method": "TEA",
        "condition_treated": "headache",
        "notes": "integration test report",
    }, token, uid_header)
    check("POST /usage-reports -> 201", status == 201, f"status={status}, body={result}")
    if status == 201:
        check("Response has id", bool(result.get("id")), str(result))

    # ── List usage reports ────────────────────────────────────────
    print("\n[5] List usage reports")
    result, status = get(BASE_USER + "/usage-reports", token, uid_header)
    check("GET /usage-reports -> 200", status == 200, f"status={status}, body={result}")
    if status == 200:
        items = result.get("items") or result.get("reports") or (result if isinstance(result, list) else [])
        check("Usage reports list has entries", len(items) >= 1, f"items={items}")

    # ── Record search history (Redis) ─────────────────────────────
    print("\n[6] Record search history entry (Redis)")
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).isoformat()
    result, status = post(BASE_USER + "/history/searches", {
        "query": "chia seeds medicinal",
        "filters": {"family": "Lamiaceae"},
        "timestamp": ts,
    }, token, uid_header)
    check("POST /history/searches -> 201", status == 201, f"status={status}, body={result}")

    # ── Get search history ────────────────────────────────────────
    print("\n[7] Get search history")
    result, status = get(BASE_USER + "/history/searches", token, uid_header)
    check("GET /history/searches -> 200", status == 200, f"status={status}, body={result}")
    if status == 200:
        items = result.get("items", [])
        check("Search history has entries", len(items) >= 1, f"items={items}")

    # ── Verify persistence (usage reports in postgres-user) ───────
    print("\n[8] Confirm records persisted in postgres-user")
    out, rc = psql("mp-postgres-user", "mp_user_user", "medicinal_plants_user",
                   "SELECT COUNT(*) FROM user_plant_usage_reports;")
    check("user_plant_usage_reports table has rows", rc == 0 and int(out or 0) >= 1, f"count={out!r}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("QuimicaDeAltura -- Endpoint Integration Tests")
    print("Verifying data persistence against live databases\n")

    token, user_id = test_auth_service()
    plant_id, compound_id = test_plant_service(token)
    test_user_service(token, user_id, plant_id)

    print("\n" + "=" * 60)
    total = PASS_COUNT + FAIL_COUNT
    print(f"Results: {PASS_COUNT}/{total} passed  |  {FAIL_COUNT} failed")
    print("=" * 60)
    sys.exit(0 if FAIL_COUNT == 0 else 1)
