from flask import Blueprint, jsonify, request
from database.db import query_db
from services.guidance_service import generate_checklist

checklist_bp = Blueprint('checklist', __name__, url_prefix='/api/checklist')

@checklist_bp.route('/generate', methods=['POST'])
def create_custom_checklist():
    """
    Accepts user demographics & application goal,
    returns tailored document requirements, fee, and timeline.
    """
    data = request.get_json() or {}
    target_service = data.get("target_service", "passport_fresh")
    age_group = data.get("age_group", "adult")
    has_10th = bool(data.get("has_10th", True))
    scheme = data.get("scheme", "normal")
    is_employed_govt = bool(data.get("is_employed_govt", False))

    result = generate_checklist(
        target_service=target_service,
        age_group=age_group,
        has_10th=has_10th,
        scheme=scheme,
        is_employed_govt=is_employed_govt
    )
    return jsonify({"status": "success", "data": result})

@checklist_bp.route('/documents', methods=['GET'])
def get_all_documents():
    """Returns official list of acceptable documents grouped by proof type."""
    proof_type = request.args.get('proof_type', '').strip()
    category = request.args.get('category', '').strip().lower()

    conditions = []
    params = []

    if proof_type:
        conditions.append("proof_type = ?")
        params.append(proof_type)

    if category:
        conditions.append("category IN (?, 'universal')")
        params.append(category)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"SELECT * FROM acceptable_documents {where_clause} ORDER BY proof_type ASC, is_popular DESC, document_name ASC"
    
    docs = query_db(sql, tuple(params))
    return jsonify({"status": "success", "count": len(docs), "data": docs})
