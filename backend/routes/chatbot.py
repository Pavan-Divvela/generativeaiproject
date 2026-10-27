from flask import Blueprint, jsonify, request
from services.rag_service import get_rag_chat_response

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chat')

@chatbot_bp.route('', methods=['POST'])
def chat():
    """
    RAG-powered conversational identity assistant endpoint.
    Retrieves grounded official guidelines and provides actionable answers.
    """
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    
    if not message:
        return jsonify({
            "status": "error",
            "message": "Message content cannot be empty."
        }), 400

    response = get_rag_chat_response(message)
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
