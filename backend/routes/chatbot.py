from flask import Blueprint, jsonify, request
from services.rag_service import get_rag_chat_response

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chat')

@chatbot_bp.route('', methods=['POST'])
def chat():
    """
    RAG-powered conversational identity assistant endpoint.
    Accepts: { "message": "...", "service": "aadhaar|pan|passport" (optional) }
    """
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    service = data.get("service", None)

    if not message:
        return jsonify({
            "status": "error",
            "message": "Message content cannot be empty."
        }), 400

    if len(message) > 1000:
        return jsonify({
            "status": "error",
            "message": "Message is too long (max 1000 characters)."
        }), 400

    # Validate service filter
    valid_services = {"aadhaar", "pan", "passport"}
    if service and service.lower() not in valid_services:
        service = None  # ignore invalid values silently
    elif service:
        service = service.lower()

    response = get_rag_chat_response(message, service=service)
    return jsonify({
        "status": "success",
        "data": response
    })

@chatbot_bp.route('/suggestions', methods=['GET'])
def suggestions():
    """Returns top recommended questions for users to get started."""
    return jsonify({
        "status": "success",
        "suggestions": [
            "How do I link PAN with Aadhaar after paying the ₹1,000 penalty?",
            "What documents are required for a Tatkaal passport?",
            "How to fix name mismatch between 10th marksheet and Aadhaar?",
            "Can I apply for an Instant e-PAN for free?",
            "What is Non-ECR status and how do I qualify?",
            "What if I have only a single name on my Aadhaar card?"
        ]
    })
