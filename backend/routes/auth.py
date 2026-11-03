"""
Authentication and Citizen Account Routes.
"""
from functools import wraps
from flask import Blueprint, jsonify, request
from services.auth_service import (
    register_user,
    authenticate_user,
    get_user_by_token,
    logout_user,
    save_user_checklist,
    get_user_checklists
)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def extract_token_from_request():
    """Extracts bearer token from Authorization header or cookie/query."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return request.args.get("token") or request.headers.get("X-Auth-Token")


def login_required(f):
    """Decorator to protect routes requiring authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = extract_token_from_request()
        if not token:
            return jsonify({
                "status": "error",
                "message": "Authentication required. Please log in."
            }), 401

        user = get_user_by_token(token)
        if not user:
            return jsonify({
                "status": "error",
                "message": "Session expired or invalid. Please log in again."
            }), 401

        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/register', methods=['POST'])
def register():
    """Registers a new citizen account."""
    data = request.get_json() or {}
    email = data.get("email")
    full_name = data.get("full_name")
    password = data.get("password")

    try:
        result = register_user(email=email, full_name=full_name, password=password)
        return jsonify({
            "status": "success",
            "message": "Account created successfully.",
            "data": result
        }), 201
    except ValueError as err:
        return jsonify({
            "status": "error",
            "message": str(err)
        }), 400
    except Exception as err:
        return jsonify({
            "status": "error",
            "message": "An error occurred while creating your account."
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticates citizen credentials and returns a session token."""
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    try:
        result = authenticate_user(email=email, password=password)
        return jsonify({
            "status": "success",
            "message": "Logged in successfully.",
            "data": result
        })
    except ValueError as err:
        return jsonify({
            "status": "error",
            "message": str(err)
        }), 401
    except Exception as err:
        return jsonify({
            "status": "error",
            "message": "Authentication service is temporarily unavailable."
        }), 500


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Returns profile information for the authenticated user."""
    user = request.current_user
    checklists = get_user_checklists(user["id"])
    return jsonify({
        "status": "success",
        "data": {
            "user": user,
            "checklists_count": len(checklists)
        }
    })


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Invalidates the active session token."""
    token = extract_token_from_request()
    if token:
        logout_user(token)
    return jsonify({
        "status": "success",
        "message": "Logged out successfully."
    })


@auth_bp.route('/checklists', methods=['GET'])
@login_required
def list_checklists():
    """Returns all saved document checklists for the current user."""
    user = request.current_user
    checklists = get_user_checklists(user["id"])
    return jsonify({
        "status": "success",
        "data": checklists
    })


@auth_bp.route('/checklists', methods=['POST'])
@login_required
def save_checklist():
    """Saves or updates a checklist for the current user."""
    data = request.get_json() or {}
    service_code = data.get("service_code")
    service_title = data.get("service_title", service_code)
    items_checked = int(data.get("items_checked", 0))
    total_items = int(data.get("total_items", 0))

    if not service_code:
        return jsonify({
            "status": "error",
            "message": "service_code is required."
        }), 400

    saved = save_user_checklist(
        user_id=request.current_user["id"],
        service_code=service_code,
        service_title=service_title,
        items_checked=items_checked,
        total_items=total_items
    )

    return jsonify({
        "status": "success",
        "message": "Checklist progress saved.",
        "data": saved
    })


@auth_bp.route('/demo-credentials', methods=['GET'])
def demo_credentials():
    """Returns test demo credentials for easy 1-click evaluation."""
    return jsonify({
        "status": "success",
        "data": {
            "email": "demo@example.com",
            "password": "Password@123",
            "name": "Demo Citizen"
        }
    })
