import os
import sys
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# Ensure backend directory and project root are in sys.path
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import Config
from database.db import init_db, is_cloud_db, query_db
from database.seed_data import seed_database
from knowledge_base.ingest import ingest_all_documents
from routes.services import services_bp
from routes.checklist import checklist_bp
from routes.chatbot import chatbot_bp
from routes.auth import auth_bp
from services.auth_service import seed_demo_user

def create_app():
    app = Flask(__name__, static_folder=None)
    CORS(app)

    # Ensure DB schema and demo user exist
    if is_cloud_db():
        init_db()
        try:
            services_row = query_db("SELECT COUNT(*) as cnt FROM services", one=True)
            if not services_row or services_row.get("cnt", 0) == 0:
                print("Cloud database is empty. Seeding services and rules...")
                seed_database()
        except Exception as e:
            print(f"Cloud DB check/seed notice: {e}")
    elif not Config.DATABASE_PATH.exists():
        print("Database not found. Initializing and seeding...")
        seed_database()
    else:
        init_db()

    try:
        seed_demo_user()
    except Exception:
        pass

    # Ensure Knowledge Base chunks exist
    if not Config.CHUNKS_FILE.exists():
        try:
            ingest_all_documents()
        except Exception as e:
            print(f"Knowledge base ingestion notice: {e}")

    # Register Blueprints
    app.register_blueprint(services_bp)
    app.register_blueprint(checklist_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(auth_bp)

    # Health check
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({
            "status": "healthy",
            "service": "Aadhaar, PAN & Passport Process Helper API",
            "version": "1.0.0"
        })

    # Serve Frontend HTML Pages & Static Assets
    @app.route('/')
    def root():
        return send_from_directory(Config.PAGES_DIR, "index.html")

    @app.route('/<path:filename>')
    def serve_frontend(filename):
        if (Config.PAGES_DIR / filename).is_file():
            return send_from_directory(Config.PAGES_DIR, filename)

        if filename.startswith("pages/"):
            sub_file = filename[len("pages/"):]
            if (Config.PAGES_DIR / sub_file).is_file():
                return send_from_directory(Config.PAGES_DIR, sub_file)

        if (Config.FRONTEND_DIR / filename).is_file():
            return send_from_directory(Config.FRONTEND_DIR, filename)

        if not filename.endswith(".html") and (Config.PAGES_DIR / f"{filename}.html").is_file():
            return send_from_directory(Config.PAGES_DIR, f"{filename}.html")

        return send_from_directory(Config.PAGES_DIR, "index.html")

    return app

# Expose WSGI application instance for production servers (gunicorn, render, etc.)
app = create_app()

def is_running_in_streamlit() -> bool:
    """Detects if script is currently being run under Streamlit."""
    try:
        import streamlit as st
        if hasattr(st, "runtime") and st.runtime.exists():
            return True
    except Exception:
        pass
    return "STREAMLIT_SERVER_PORT" in os.environ or any("streamlit" in str(arg).lower() for arg in sys.argv)


def run_streamlit_portal():
    """Renders the Streamlit Citizen Helper UI when loaded on Streamlit Community Cloud."""
    import streamlit as st
    from services.rag_service import get_rag_chat_response
    from services.guidance_service import generate_checklist, analyze_name_discrepancy

    st.set_page_config(
        page_title="Aadhaar, PAN & Passport Helper",
        page_icon="🇮🇳",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🇮🇳 Aadhaar, PAN & Passport Process Helper")
    st.caption("Citizen Guidance Portal with Evidence-Grounded RAG AI Assistant, Document Checklists & Rule Verification")

    with st.sidebar:
        st.header("📌 Official Portals")
        st.markdown("- [myAadhaar Portal (UIDAI)](https://myaadhaar.uidai.gov.in/)")
        st.markdown("- [Income Tax e-Filing (PAN)](https://www.incometax.gov.in/)")
        st.markdown("- [Protean NSDL PAN Portal](https://www.onlineservices.nsdl.com/)")
        st.markdown("- [Passport Seva Portal](https://www.passportindia.gov.in/)")
        st.divider()
        st.info("💡 All recommendations and answers are grounded in official UIDAI, Income Tax Department, and MEA circulars.")

    tab_chat, tab_services, tab_checklist, tab_discrepancy = st.tabs([
        "💬 AI Assistant (RAG)",
        "📑 Services & Official Fees",
        "✅ Document Checklist",
        "⚠️ Name Discrepancy Resolver"
    ])

    # TAB 1: RAG CHATBOT
    with tab_chat:
        st.subheader("💬 Ask Any Question on Aadhaar, PAN or Passport")
        st.write("Get evidence-grounded guidance with exact source circulars, verified fees, and official links.")

        col1, col2 = st.columns([3, 1])
        with col1:
            user_query = st.text_input(
                "Your Question:",
                placeholder="e.g. Can I use a rent agreement as address proof for Passport and Aadhaar?",
                key="st_chat_query_input"
            )
        with col2:
            service_filter = st.selectbox(
                "Filter Service:",
                ["All Services", "Aadhaar", "PAN", "Passport"],
                index=0
            )

        st.caption("Common queries:")
        col_s1, col_s2, col_s3 = st.columns(3)
        if col_s1.button("Why does PAN-Aadhaar linking fail?"):
            user_query = "Why does PAN-Aadhaar linking fail with demographic mismatch error?"
        if col_s2.button("Tatkaal Passport documents required"):
            user_query = "What documents are required for fresh Passport under Tatkaal scheme?"
        if col_s3.button("Limits on changing Aadhaar name & DoB"):
            user_query = "How many times can I change Name and Date of Birth in Aadhaar?"

        if st.button("Get Verified Answer", type="primary") and user_query:
            svc = None if service_filter == "All Services" else service_filter.lower()
            with st.spinner("Searching official government circulars and generating response..."):
                try:
                    response = get_rag_chat_response(user_query, service=svc)
                    st.markdown("### 📋 Guidance:")
                    st.markdown(response.get("answer", "No answer found."))

                    citations = response.get("citations", [])
                    if citations:
                        with st.expander(f"📚 Verified Sources & Circular Citations ({len(citations)})", expanded=True):
                            for cite in citations:
                                doc_title = cite.get("document_title") or cite.get("source_file", "Official Document")
                                url = cite.get("official_url", "#")
                                excerpt = cite.get("excerpt", "")
                                page = cite.get("page", None)
                                page_str = f" (Page {page})" if page else ""
                                st.markdown(f"**[{doc_title}]({url})**{page_str}")
                                if excerpt:
                                    st.caption(f'"{excerpt[:300]}..."')
                except Exception as e:
                    st.error(f"Error fetching response: {str(e)}")

    # TAB 2: SERVICES & FEES
    with tab_services:
        st.subheader("📑 Official Government Services, Modes & Fees")
        category = st.radio("Select Category:", ["All", "Aadhaar", "PAN", "Passport"], horizontal=True)

        if category == "All":
            services = query_db("SELECT * FROM services ORDER BY category, id")
        else:
            services = query_db("SELECT * FROM services WHERE category = ? ORDER BY id", (category.lower(),))

        if services:
            for s in services:
                with st.container(border=True):
                    c_title, c_mode, c_fee = st.columns([3, 1, 1])
                    c_title.markdown(f"### {s['title']}")
                    c_mode.metric(label="Application Mode", value=s['mode'])
                    c_fee.metric(label="Official Fee", value=s['fee'])
                    st.write(s['description'])
                    st.caption(f"⏱️ **Standard Processing Time:** {s['timeline']}")
                    st.markdown(f"🔗 [Visit Official Portal]({s['official_url']})")
        else:
            st.info("No services found in this category.")

    # TAB 3: DOCUMENT CHECKLIST
    with tab_checklist:
        st.subheader("✅ Personalized Document Checklist Generator")
        c1, c2, c3 = st.columns(3)
        with c1:
            target_service = st.selectbox(
                "Target Service:",
                [
                    ("aadhaar_fresh", "Aadhaar - Fresh Enrollment"),
                    ("aadhaar_demo_update", "Aadhaar - Address / Name Update"),
                    ("pan_instant_epan", "PAN - Instant e-PAN"),
                    ("pan_new_form49a", "PAN - New Form 49A"),
                    ("passport_fresh_normal", "Passport - Fresh Normal"),
                    ("passport_fresh_tatkaal", "Passport - Fresh Tatkaal")
                ],
                format_func=lambda x: x[1]
            )[0]
        with c2:
            age_group = st.selectbox("Applicant Age Group:", ["adult", "minor_above_5", "minor_below_5"])
        with c3:
            has_10th = st.checkbox("Holds 10th Standard Certificate (Non-ECR)", value=True)

        if st.button("Generate Checklist", key="st_btn_gen_checklist"):
            checklist_result = generate_checklist(target_service=target_service, age_group=age_group, has_10th=has_10th)
            st.success(f"**Checklist generated for {checklist_result.get('service_title', target_service)}**")
            st.markdown(f"**Mode**: {checklist_result.get('mode', 'N/A')} | **Official Fee**: {checklist_result.get('official_fee', 'N/A')} | **Timeline**: {checklist_result.get('estimated_timeline', 'N/A')}")
            st.markdown(f"🔗 [Official Application Link]({checklist_result.get('official_portal', '#')})")

            steps = checklist_result.get("steps", [])
            if steps:
                st.markdown("#### 📝 Step-by-Step Instructions:")
                for i, step in enumerate(steps, 1):
                    st.markdown(f"{i}. {step}")

            docs = checklist_result.get("required_documents", {})
            if docs:
                st.markdown("#### 📂 Acceptable Documents:")
                for group, doc_list in docs.items():
                    st.markdown(f"**{group.upper()}**: {', '.join(doc_list) if isinstance(doc_list, list) else doc_list}")

    # TAB 4: DISCREPANCY RESOLVER
    with tab_discrepancy:
        st.subheader("⚠️ Document Mismatch & Discrepancy Analyzer")
        d_col1, d_col2, d_col3 = st.columns(3)
        with d_col1:
            name_10th = st.text_input("Name on 10th / Birth Certificate:", value="Ramesh Kumar Sharma")
            dob_10th = st.text_input("DoB on 10th Certificate (DD/MM/YYYY):", value="15/08/1995")
        with d_col2:
            name_aadhaar = st.text_input("Name on Aadhaar Card:", value="Ramesh K Sharma")
            dob_aadhaar = st.text_input("DoB on Aadhaar (DD/MM/YYYY):", value="15/08/1995")
        with d_col3:
            name_pan = st.text_input("Name on PAN Card:", value="Ramesh Kumar Sharma")
            dob_pan = st.text_input("DoB on PAN (DD/MM/YYYY):", value="15/08/1995")

        if st.button("Analyze Discrepancy", type="primary", key="st_btn_discrepancy"):
            result = analyze_name_discrepancy(
                name_10th=name_10th,
                name_aadhaar=name_aadhaar,
                name_pan=name_pan,
                dob_10th=dob_10th,
                dob_aadhaar=dob_aadhaar,
                dob_pan=dob_pan
            )
            sev = result.get("overall_severity", "LOW")
            if sev == "HIGH":
                st.error(f"Overall Severity: **{sev}** - Risk of government application rejection or PAN inoperative.")
            elif sev == "MEDIUM":
                st.warning(f"Overall Severity: **{sev}** - Discrepancy detected that may cause delays.")
            else:
                st.success(f"Overall Severity: **{sev}** - Details are consistent across documents.")

            issues = result.get("issues_detected", [])
            if issues:
                st.markdown("#### 🔍 Issues Detected:")
                for issue in issues:
                    st.markdown(f"- **{issue.get('issue')}** (Severity: `{issue.get('severity')}`): {issue.get('description')}")

            recommendations = result.get("resolution_steps", [])
            if recommendations:
                st.markdown("#### 🛠️ Recommended Resolution Steps:")
                for r in recommendations:
                    st.markdown(f"1. {r}")


# Main Entry Point
if is_running_in_streamlit():
    run_streamlit_portal()
elif __name__ == '__main__':
    print(f"🚀 Starting Aadhaar, PAN & Passport Process Helper on http://127.0.0.1:{Config.PORT}")
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG, use_reloader=False)
