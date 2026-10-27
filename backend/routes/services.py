from flask import Blueprint, jsonify, request
from database.db import query_db
from services.guidance_service import analyze_name_discrepancy

services_bp = Blueprint('services', __name__, url_prefix='/api')

@services_bp.route('/services', methods=['GET'])
def get_services():
    """Returns services list, optionally filtered by category (aadhaar, pan, passport)."""
    category = request.args.get('category', '').strip().lower()
    if category:
        sql = "SELECT * FROM services WHERE category = ? ORDER BY id ASC"
        services = query_db(sql, (category,))
    else:
        sql = "SELECT * FROM services ORDER BY category ASC, id ASC"
        services = query_db(sql)
    
    return jsonify({"status": "success", "count": len(services), "data": services})

@services_bp.route('/services/<service_code>', methods=['GET'])
def get_service_detail(service_code):
    """Returns details for a specific service by code."""
    sql = "SELECT * FROM services WHERE code = ?"
    service = query_db(sql, (service_code,), one=True)
    if not service:
        return jsonify({"status": "error", "message": f"Service '{service_code}' not found."}), 404

    # Fetch associated acceptable documents
    docs_sql = "SELECT * FROM acceptable_documents WHERE category IN (?, 'universal') ORDER BY proof_type ASC, is_popular DESC"
    docs = query_db(docs_sql, (service['category'],))

    return jsonify({
        "status": "success",
        "service": service,
        "acceptable_documents": docs
    })

@services_bp.route('/services/analyze-mismatch', methods=['POST'])
def analyze_mismatch():
    """
    Analyzes names and dates of birth across 10th cert, Aadhaar, and PAN.
    Returns legal diagnosis and prioritized correction roadmap.
    """
    data = request.get_json() or {}
    name_10th = data.get("name_10th", "")
    name_aadhaar = data.get("name_aadhaar", "")
    name_pan = data.get("name_pan", "")
    dob_10th = data.get("dob_10th", "")
    dob_aadhaar = data.get("dob_aadhaar", "")
    dob_pan = data.get("dob_pan", "")

    result = analyze_name_discrepancy(
        name_10th=name_10th,
        name_aadhaar=name_aadhaar,
        name_pan=name_pan,
        dob_10th=dob_10th,
        dob_aadhaar=dob_aadhaar,
        dob_pan=dob_pan
    )
    return jsonify(result)

@services_bp.route('/faqs', methods=['GET'])
def get_faqs():
    """Searches and returns FAQs by category or search term."""
    category = request.args.get('category', '').strip().lower()
    search = request.args.get('q', '').strip().lower()

    params = []
    conditions = []

    if category:
        conditions.append("category = ?")
        params.append(category)

    if search:
        conditions.append("(question LIKE ? OR answer LIKE ? OR tags LIKE ?)")
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard])

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"SELECT * FROM faqs {where_clause} ORDER BY id ASC"
    
    faqs = query_db(sql, tuple(params))
    return jsonify({"status": "success", "count": len(faqs), "data": faqs})
