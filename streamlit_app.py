"""
Aadhaar, PAN & Passport Process Helper - Streamlit Web Application
Matches the custom HTML/CSS DocProcess Helper portal design and provides citizen auth.
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# Setup module path
root_dir = Path(__file__).resolve().parent
if (root_dir / "backend").exists():
    backend_dir = root_dir / "backend"
    project_root = root_dir
elif (root_dir / "aadhaar-pan-passport-helper" / "backend").exists():
    backend_dir = root_dir / "aadhaar-pan-passport-helper" / "backend"
    project_root = root_dir / "aadhaar-pan-passport-helper"
else:
    backend_dir = root_dir
    project_root = root_dir

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
from config import Config
from database.db import init_db, is_cloud_db, query_db
from database.seed_data import seed_database
from knowledge_base.ingest import ingest_all_documents
from services.rag_service import get_rag_chat_response
from services.guidance_service import generate_checklist, analyze_name_discrepancy
from services.auth_service import authenticate_user, register_user, get_user_checklists, save_user_checklist

# Page Configuration
st.set_page_config(
    page_title="DocProcess Helper | Aadhaar, PAN & Passport",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Backend
@st.cache_resource(show_spinner="Initializing Database and Circulars...")
def bootstrap_app():
    if is_cloud_db():
        init_db()
        try:
            services_row = query_db("SELECT COUNT(*) as cnt FROM services", one=True)
            if not services_row or services_row.get("cnt", 0) == 0:
                seed_database()
        except Exception:
            pass
    elif not Config.DATABASE_PATH.exists():
        seed_database()
    else:
        init_db()

    if not Config.CHUNKS_FILE.exists():
        try:
            ingest_all_documents()
        except Exception:
            pass
    return True

bootstrap_app()

# Session State for Page and Authentication
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

# Custom CSS matching DocProcess Helper design system
st.markdown("""
<style>
  /* Hide Streamlit default chrome */
  #MainMenu, header, footer { visibility: hidden; height: 0; }
  [data-testid="stSidebar"] { display: none; }
  .block-container {
    padding-top: 0.5rem;
    padding-bottom: 3rem;
    max-width: 1240px;
    margin: 0 auto;
  }

  /* Typography & Base */
  body, .stMarkdown, p, div {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1e293b;
  }

  /* Advisory bar */
  .gov-disclaimer {
    background: #eff6ff;
    border-bottom: 1px solid #bfdbfe;
    color: #1e40af;
    padding: 6px 14px;
    font-size: 0.8rem;
    text-align: center;
    border-radius: 6px;
    margin-bottom: 10px;
  }

  /* Brand and Header */
  .header-brand {
    display: inline-flex;
    align-items: center;
    gap: 10px;
  }
  .brand-in-badge {
    background: #1e3a8a;
    color: #ffffff;
    font-weight: 800;
    font-size: 1.1rem;
    padding: 4px 10px;
    border-radius: 8px;
    letter-spacing: 0.5px;
    display: inline-block;
  }
  .brand-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.5px;
  }

  /* Hero Section */
  .hero-container {
    text-align: center;
    padding: 30px 15px 25px 15px;
    max-width: 900px;
    margin: 0 auto;
  }
  .hero-badge {
    display: inline-flex;
    align-items: center;
    background: #eff6ff;
    color: #1d4ed8;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 600;
    margin-bottom: 14px;
    border: 1px solid #dbeafe;
  }
  .hero-heading {
    font-size: 2.5rem;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.8px;
    line-height: 1.2;
    margin-bottom: 12px;
  }
  .hero-subtext {
    font-size: 1.05rem;
    color: #475569;
    line-height: 1.6;
    margin-bottom: 24px;
  }

  /* Cards */
  .service-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 22px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .card-icon-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 38px;
    height: 38px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.9rem;
    margin-bottom: 12px;
  }
  .badge-blue { background: #dbeafe; color: #1e40af; }
  .badge-orange { background: #ffedd5; color: #c2410c; }
  .badge-emerald { background: #d1fae5; color: #065f46; }
  
  .card-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 8px;
  }
  .card-desc {
    font-size: 0.92rem;
    color: #475569;
    line-height: 1.5;
    margin-bottom: 14px;
  }
  .pill-tag {
    display: inline-block;
    background: #f1f5f9;
    color: #334155;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    margin-right: 5px;
    margin-bottom: 6px;
    font-weight: 500;
  }

  /* Tool Box / Mismatch Form */
  .mismatch-box {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 28px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    margin-top: 30px;
    margin-bottom: 30px;
  }
  .mismatch-heading {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 1.35rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 6px;
  }
  .mismatch-subtext {
    font-size: 0.92rem;
    color: #64748b;
    margin-bottom: 20px;
    line-height: 1.5;
  }

  /* Footer Cards */
  .footer-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 22px;
    height: 100%;
  }
  .footer-card-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .footer-card-desc {
    font-size: 0.9rem;
    color: #475569;
    line-height: 1.5;
    margin-bottom: 12px;
  }
  .footer-card-link {
    font-size: 0.88rem;
    font-weight: 600;
    color: #2563eb;
    text-decoration: none;
  }

  /* Buttons */
  div.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s ease;
  }
  .stButton button[kind="primary"] {
    background-color: #ea580c !important;
    border-color: #ea580c !important;
    color: white !important;
  }
</style>
""", unsafe_allow_html=True)

# ----------------- TOP NAVBAR -----------------
st.markdown("""
<div class="gov-disclaimer">
  🛡️ <strong>Public Advisory:</strong> Independent citizen assistance platform. Not affiliated with UIDAI, Income Tax Dept, or MEA. Verify official submissions on UIDAI, Protean, or Passport Seva portals.
</div>
""", unsafe_allow_html=True)

# Navigation Bar Layout
nav_c1, nav_c2, nav_c3, nav_c4, nav_c5, nav_c6, nav_c7, nav_c8 = st.columns([2.5, 0.9, 1.1, 1.1, 1.3, 0.9, 1.3, 1.3])

with nav_c1:
    st.markdown("""
    <div class="header-brand">
      <span class="brand-in-badge">IN</span>
      <span class="brand-title">DocProcess Helper</span>
    </div>
    """, unsafe_allow_html=True)

with nav_c2:
    if st.button("Home", key="nav_home", use_container_width=True):
        st.session_state.current_page = "home"
        st.rerun()

with nav_c3:
    if st.button("Aadhaar", key="nav_aadhaar", use_container_width=True):
        st.session_state.current_page = "aadhaar"
        st.rerun()

with nav_c4:
    if st.button("PAN Card", key="nav_pan", use_container_width=True):
        st.session_state.current_page = "pan"
        st.rerun()

with nav_c5:
    if st.button("Passport", key="nav_passport", use_container_width=True):
        st.session_state.current_page = "passport"
        st.rerun()

with nav_c6:
    if st.button("FAQs", key="nav_faqs", use_container_width=True):
        st.session_state.current_page = "faqs"
        st.rerun()

with nav_c7:
    if st.button("🤖 AI Assistant", key="nav_ai", type="primary", use_container_width=True):
        st.session_state.current_page = "chatbot"
        st.rerun()

with nav_c8:
    if st.session_state.auth_user:
        user_name = st.session_state.auth_user.get("full_name", "Citizen").split()[0]
        if st.button(f"👤 {user_name}", key="nav_user_profile", use_container_width=True):
            st.session_state.current_page = "dashboard"
            st.rerun()
    else:
        if st.button("🔐 Sign In", key="nav_signin", use_container_width=True):
            st.session_state.current_page = "login"
            st.rerun()

st.divider()

# ----------------- PAGE ROUTER -----------------
current_page = st.session_state.current_page

# ================= PAGE 1: HOME =================
if current_page == "home":
    # Hero Section
    st.markdown("""
    <div class="hero-container">
      <div class="hero-badge">✨ Smart Citizen Assistance Platform</div>
      <h1 class="hero-heading">Aadhaar, PAN & Passport Process Helper</h1>
      <p class="hero-subtext">
        Eliminate application rejections, mismatched names, and wasted center appointments. 
        Get step-by-step guidance, personalized document checklists, and cross-document discrepancy diagnosis.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Hero Action Buttons
    h_b1, h_b2, h_b3 = st.columns([1, 1, 1])
    with h_b1:
        if st.button("🔍 Check Name Mismatch", type="primary", use_container_width=True, key="hero_btn_mismatch"):
            st.session_state.scroll_to_mismatch = True
    with h_b2:
        if st.button("💬 Ask AI Assistant", use_container_width=True, key="hero_btn_ai"):
            st.session_state.current_page = "chatbot"
            st.rerun()
    with h_b3:
        if st.button("📖 View Golden Order Roadmap", use_container_width=True, key="hero_btn_roadmap"):
            st.session_state.current_page = "roadmap"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 3 Service Cards
    card1, card2, card3 = st.columns(3)

    with card1:
        st.markdown("""
        <div class="service-card">
          <div>
            <div class="card-icon-badge badge-blue">ID</div>
            <div class="card-title">Aadhaar Services</div>
            <div class="card-desc">
              The universal biometric foundation. Learn about demographic corrections, mandatory updates for children at ages 5 & 15, and PVC cards.
            </div>
            <div>
              <span class="pill-tag">UIDAI Portal</span>
              <span class="pill-tag">Demographics</span>
              <span class="pill-tag">Biometric MBU</span>
              <span class="pill-tag">Masked e-Aadhaar</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Explore Aadhaar Guide →", key="btn_card_aadhaar", use_container_width=True):
            st.session_state.current_page = "aadhaar"
            st.rerun()

    with card2:
        st.markdown("""
        <div class="service-card">
          <div>
            <div class="card-icon-badge badge-orange">💳</div>
            <div class="card-title">PAN Card Services</div>
            <div class="card-desc">
              Permanent Account Number for tax and banking. Instant free e-PAN, PAN-Aadhaar linking resolution, and Form 49A corrections.
            </div>
            <div>
              <span class="pill-tag">Instant e-PAN (Free)</span>
              <span class="pill-tag">PAN-Aadhaar Link</span>
              <span class="pill-tag">Minor Head 500</span>
              <span class="pill-tag">Protean/NSDL</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Explore PAN Guide →", key="btn_card_pan", use_container_width=True):
            st.session_state.current_page = "pan"
            st.rerun()

    with card3:
        st.markdown("""
        <div class="service-card">
          <div>
            <div class="card-icon-badge badge-emerald">🛂</div>
            <div class="card-title">Passport Seva</div>
            <div class="card-desc">
              Ministry of External Affairs services. Normal vs. Tatkaal schemes, Non-ECR qualification rules, and Police Verification readiness.
            </div>
            <div>
              <span class="pill-tag">Normal vs Tatkaal</span>
              <span class="pill-tag">Non-ECR Matrix</span>
              <span class="pill-tag">PSK Counter Guide</span>
              <span class="pill-tag">Police Verification</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Explore Passport Guide →", key="btn_card_passport", use_container_width=True):
            st.session_state.current_page = "passport"
            st.rerun()

    # Mismatch Analyzer Tool Section (Matching First Image)
    st.markdown("""
    <div class="mismatch-box">
      <div class="mismatch-heading">⚡ Cross-Document Name & DoB Mismatch Analyzer</div>
      <div class="mismatch-subtext">
        Over 65% of passport rejections and PAN-Aadhaar linking failures happen because of minor spelling or birthdate differences. Enter your details below to check for potential blockers before applying.
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        m_row1_c1, m_row1_c2 = st.columns(2)
        with m_row1_c1:
            name_10th = st.text_input(
                "Name on 10th Certificate / Birth Cert (Anchor):",
                placeholder="e.g., RAMESH KUMAR SHARMA",
                value="RAMESH KUMAR SHARMA",
                key="home_input_10th_name"
            )
        with m_row1_c2:
            dob_10th = st.text_input(
                "Date of Birth on 10th / Birth Cert:",
                placeholder="dd-mm-yyyy",
                value="15-08-1995",
                key="home_input_10th_dob"
            )

        m_row2_c1, m_row2_c2 = st.columns(2)
        with m_row2_c1:
            name_aadhaar = st.text_input(
                "Name on Current Aadhaar Card:",
                placeholder="e.g., R. K. SHARMA or RAMESH SHARMA",
                value="R. K. SHARMA",
                key="home_input_aadhaar_name"
            )
        with m_row2_c2:
            dob_aadhaar = st.text_input(
                "Date of Birth on Aadhaar Card:",
                placeholder="dd-mm-yyyy",
                value="15-08-1995",
                key="home_input_aadhaar_dob"
            )

        m_row3_c1, m_row3_c2 = st.columns(2)
        with m_row3_c1:
            name_pan = st.text_input(
                "Name on Current PAN Card (Optional if not yet created):",
                placeholder="e.g., RAMESH KUMAR SHARMA",
                value="RAMESH KUMAR SHARMA",
                key="home_input_pan_name"
            )
        with m_row3_c2:
            dob_pan = st.text_input(
                "Date of Birth on PAN Card:",
                placeholder="dd-mm-yyyy",
                value="15-08-1995",
                key="home_input_pan_dob"
            )

        if st.button("Run Discrepancy Check & Generate Legal Roadmap", type="primary", use_container_width=True, key="home_btn_check_mismatch"):
            analysis = analyze_name_discrepancy(
                name_10th=name_10th,
                name_aadhaar=name_aadhaar,
                name_pan=name_pan,
                dob_10th=dob_10th,
                dob_aadhaar=dob_aadhaar,
                dob_pan=dob_pan
            )

            severity = analysis.get("overall_severity", "LOW")
            if severity == "HIGH":
                st.error("🚨 **High Severity Discrepancy Detected** — Immediate risk of PAN-Aadhaar linking penalty or Passport rejection at PSK.")
            elif severity == "MEDIUM":
                st.warning("⚠️ **Medium Severity Discrepancy Detected** — May cause processing delays or require an Annexure affidavit.")
            else:
                st.success("✅ **Details are Aligned Across Documents** — Good to proceed with official applications!")

            issues = analysis.get("issues_detected", [])
            if issues:
                st.markdown("#### 🔍 Discrepancies Found:")
                for issue in issues:
                    st.markdown(f"- **{issue.get('issue')}** (`{issue.get('severity')}`): {issue.get('description')}")

            steps = analysis.get("resolution_steps", [])
            if steps:
                st.markdown("#### 🛠️ Recommended Action Roadmap:")
                for step in steps:
                    st.markdown(f"- {step}")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2 Bottom Feature Cards
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        st.markdown("""
        <div class="footer-card">
          <div class="footer-card-title">🔵 The Golden Order Sequence</div>
          <div class="footer-card-desc">
            Never apply for a Passport or link PAN-Aadhaar without verifying that your root document matches. Our tested 4-step sequence ensures you never pay double fees or encounter rejected appointments at Passport Seva Kendras.
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Read the complete Golden Order guide →", key="btn_read_golden"):
            st.session_state.current_page = "roadmap"
            st.rerun()

    with b_col2:
        st.markdown("""
        <div class="footer-card">
          <div class="footer-card-title">⚪ Grounded AI Knowledge Assistant</div>
          <div class="footer-card-desc">
            Have questions about the ₹1,000 late fee challan under Minor Head 500, Tatkaal 3-document proof requirements, or single-name issues? Chat with our specialized RAG assistant grounded on official gazettes and UIDAI regulations.
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start interactive consultation →", key="btn_start_ai"):
            st.session_state.current_page = "chatbot"
            st.rerun()

# ================= PAGE 2: SIGN IN / REGISTRATION =================
elif current_page == "login":
    st.markdown("""
    <div style="text-align:center; max-width:550px; margin: 0 auto; padding: 20px 0;">
      <h2 style="font-weight:800; font-size:2rem; color:#0f172a; margin-bottom: 6px;">🔐 Citizen Identity Access</h2>
      <p style="color:#64748b; font-size:0.95rem;">Sign in to save document checklists, track your application roadmaps, and manage your progress.</p>
    </div>
    """, unsafe_allow_html=True)

    login_col1, login_col2, login_col3 = st.columns([1, 2, 1])
    with login_col2:
        auth_tab1, auth_tab2 = st.tabs(["Sign In to Existing Account", "Create New Citizen Account"])

        with auth_tab1:
            st.info("💡 **Demo Account Available**: `demo@example.com` / `Password@123`")
            if st.button("⚡ Fill Demo Credentials", key="btn_fill_demo"):
                st.session_state.login_email = "demo@example.com"
                st.session_state.login_password = "Password@123"

            login_email = st.text_input(
                "Email Address",
                value=st.session_state.get("login_email", ""),
                placeholder="citizen@example.com",
                key="input_login_email"
            )
            login_password = st.text_input(
                "Password",
                value=st.session_state.get("login_password", ""),
                type="password",
                placeholder="••••••••",
                key="input_login_password"
            )

            if st.button("Sign In", type="primary", use_container_width=True, key="btn_do_login"):
                try:
                    res = authenticate_user(login_email, login_password)
                    st.session_state.auth_user = res["user"]
                    st.session_state.auth_token = res["token"]
                    st.success(f"Welcome back, {res['user']['full_name']}!")
                    st.session_state.current_page = "dashboard"
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

        with auth_tab2:
            reg_name = st.text_input("Full Name (as per documents)", placeholder="e.g., Rajesh Kumar", key="reg_name")
            reg_email = st.text_input("Email Address", placeholder="rajesh@example.com", key="reg_email")
            reg_password = st.text_input("Password (min 6 characters)", type="password", key="reg_password")

            if st.button("Create Account & Sign In", type="primary", use_container_width=True, key="btn_do_reg"):
                try:
                    res = register_user(reg_email, reg_name, reg_password)
                    st.session_state.auth_user = res["user"]
                    st.session_state.auth_token = res["token"]
                    st.success(f"Account created! Welcome, {res['user']['full_name']}!")
                    st.session_state.current_page = "dashboard"
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

# ================= PAGE 3: DASHBOARD =================
elif current_page == "dashboard":
    user = st.session_state.auth_user
    if not user:
        st.session_state.current_page = "login"
        st.rerun()

    d_h1, d_h2 = st.columns([3, 1])
    with d_h1:
        st.title(f"👤 Welcome, {user.get('full_name')}")
        st.caption(f"Citizen ID: `#{user.get('id')}` | Account: `{user.get('email')}`")
    with d_h2:
        if st.button("🚪 Sign Out", key="btn_signout", use_container_width=True):
            st.session_state.auth_user = None
            st.session_state.auth_token = None
            st.session_state.current_page = "home"
            st.rerun()

    st.markdown("### 📋 Your Saved Checklists & Progress")
    checklists = get_user_checklists(user["id"])

    if checklists:
        for c in checklists:
            with st.container(border=True):
                pct = int((c['items_checked'] / max(c['total_items'], 1)) * 100)
                st.markdown(f"**{c['service_title']}** — {c['items_checked']}/{c['total_items']} items checked ({pct}%)")
                st.progress(pct / 100)
                st.caption(f"Last updated: {c.get('updated_at', 'Recently')}")
    else:
        st.info("You don't have any saved checklists yet. Generate one from the Aadhaar, PAN, or Passport guide to track your progress!")

# ================= PAGE 4: AI ASSISTANT (RAG) =================
elif current_page == "chatbot":
    st.markdown("""
    <div style="text-align:center; max-width:800px; margin: 0 auto; padding-bottom: 20px;">
      <h2 style="font-weight:800; font-size:2.2rem; color:#0f172a;">🤖 Grounded AI Process Assistant</h2>
      <p style="color:#64748b; font-size:1rem;">Ask factual questions on Aadhaar updates, PAN corrections, Tatkaal passport schemes, and late fee challans. Every response cites verified government circulars.</p>
    </div>
    """, unsafe_allow_html=True)

    col_q, col_s = st.columns([3, 1])
    with col_q:
        chat_q = st.text_input(
            "Your Question:",
            placeholder="e.g. Can I use a rent agreement as address proof for Passport and Aadhaar?",
            key="page_chat_q"
        )
    with col_s:
        chat_svc = st.selectbox(
            "Filter Service:",
            ["All Services", "Aadhaar", "PAN", "Passport"],
            key="page_chat_svc"
        )

    st.caption("Common queries:")
    q1, q2, q3 = st.columns(3)
    if q1.button("Why does PAN-Aadhaar linking fail?", key="chip_q1"):
        chat_q = "Why does PAN-Aadhaar linking fail with demographic mismatch error?"
    if q2.button("Tatkaal Passport documents required", key="chip_q2"):
        chat_q = "What documents are required for fresh Passport under Tatkaal scheme?"
    if q3.button("Limits on changing Aadhaar name & DoB", key="chip_q3"):
        chat_q = "How many times can I change Name and Date of Birth in Aadhaar?"

    if st.button("Ask AI Assistant", type="primary", use_container_width=True, key="btn_ask_rag") and chat_q:
        svc_arg = None if chat_svc == "All Services" else chat_svc.lower()
        with st.spinner("Searching official gazettes & generating answer..."):
            try:
                resp = get_rag_chat_response(chat_q, service=svc_arg)
                st.markdown("### 📋 Official Guidance:")
                st.markdown(resp.get("answer", "No answer found."))

                citations = resp.get("citations", [])
                if citations:
                    with st.expander(f"📚 Verified Sources & Official Circulars ({len(citations)})", expanded=True):
                        for cite in citations:
                            doc_title = cite.get("document_title") or cite.get("source_file", "Official Circular")
                            url = cite.get("official_url", "#")
                            excerpt = cite.get("excerpt", "")
                            page = cite.get("page", None)
                            page_str = f" (Page {page})" if page else ""
                            st.markdown(f"**[{doc_title}]({url})**{page_str}")
                            if excerpt:
                                st.caption(f'"{excerpt[:300]}..."')
            except Exception as e:
                st.error(f"Error fetching answer: {str(e)}")

# ================= PAGE 5: AADHAAR GUIDE =================
elif current_page == "aadhaar":
    st.title("🆔 Aadhaar Services Guide & Checklist")
    st.caption("Official requirements for fresh enrollment, address updates, biometric updates, and PVC cards.")

    services = query_db("SELECT * FROM services WHERE category = 'aadhaar' ORDER BY id")
    for s in services:
        with st.container(border=True):
            st.markdown(f"### {s['title']}")
            st.markdown(f"**Mode**: `{s['mode']}` | **Fee**: `{s['fee']}` | **Timeline**: `{s['timeline']}`")
            st.write(s['description'])
            st.markdown(f"🔗 [Official Portal Link]({s['official_url']})")

    st.markdown("---")
    st.subheader("✅ Generate Aadhaar Document Checklist")
    a_type = st.selectbox("Select Application Type:", [
        ("aadhaar_fresh", "Fresh Aadhaar Enrollment (Ages 18+)"),
        ("aadhaar_demo_update", "Demographic Update (Address, Name, DoB)")
    ], format_func=lambda x: x[1])[0]

    if st.button("Generate Aadhaar Checklist", type="primary", key="btn_gen_aadhaar_chk"):
        chk = generate_checklist(target_service=a_type)
        st.success(f"Checklist created for {chk.get('service_title')}")
        for i, step in enumerate(chk.get("steps", []), 1):
            st.markdown(f"{i}. {step}")
        st.markdown("#### Acceptable Proofs:")
        for k, v in chk.get("required_documents", {}).items():
            st.markdown(f"**{k.upper()}**: {', '.join(v) if isinstance(v, list) else v}")

# ================= PAGE 6: PAN CARD GUIDE =================
elif current_page == "pan":
    st.title("💳 PAN Card Services & Linking Guide")
    st.caption("Instant e-PAN allotment, physical PAN Card Form 49A, and Section 234H linking penalty rules.")

    services = query_db("SELECT * FROM services WHERE category = 'pan' ORDER BY id")
    for s in services:
        with st.container(border=True):
            st.markdown(f"### {s['title']}")
            st.markdown(f"**Mode**: `{s['mode']}` | **Fee**: `{s['fee']}` | **Timeline**: `{s['timeline']}`")
            st.write(s['description'])
            st.markdown(f"🔗 [Official Portal Link]({s['official_url']})")

    st.markdown("---")
    st.subheader("✅ Generate PAN Document Checklist")
    p_type = st.selectbox("Select Application Type:", [
        ("pan_instant_epan", "Instant e-PAN via Aadhaar e-KYC (Free)"),
        ("pan_new_form49a", "New Physical PAN Card (Form 49A)")
    ], format_func=lambda x: x[1])[0]

    if st.button("Generate PAN Checklist", type="primary", key="btn_gen_pan_chk"):
        chk = generate_checklist(target_service=p_type)
        st.success(f"Checklist created for {chk.get('service_title')}")
        for i, step in enumerate(chk.get("steps", []), 1):
            st.markdown(f"{i}. {step}")

# ================= PAGE 7: PASSPORT SEVA GUIDE =================
elif current_page == "passport":
    st.title("🛂 Passport Seva Guide & Checklist")
    st.caption("Normal vs Tatkaal scheme, Non-ECR requirements, and Police Verification procedures.")

    services = query_db("SELECT * FROM services WHERE category = 'passport' ORDER BY id")
    for s in services:
        with st.container(border=True):
            st.markdown(f"### {s['title']}")
            st.markdown(f"**Mode**: `{s['mode']}` | **Fee**: `{s['fee']}` | **Timeline**: `{s['timeline']}`")
            st.write(s['description'])
            st.markdown(f"🔗 [Official Portal Link]({s['official_url']})")

    st.markdown("---")
    st.subheader("✅ Generate Passport Document Checklist")
    pass_type = st.selectbox("Select Scheme:", [
        ("passport_fresh_normal", "Fresh Passport (Normal Scheme — ₹1,500)"),
        ("passport_fresh_tatkaal", "Fresh Passport (Tatkaal Scheme — ₹3,500)")
    ], format_func=lambda x: x[1])[0]

    if st.button("Generate Passport Checklist", type="primary", key="btn_gen_pass_chk"):
        chk = generate_checklist(target_service=pass_type)
        st.success(f"Checklist created for {chk.get('service_title')}")
        for i, step in enumerate(chk.get("steps", []), 1):
            st.markdown(f"{i}. {step}")
        st.markdown("#### Acceptable Proofs:")
        for k, v in chk.get("required_documents", {}).items():
            st.markdown(f"**{k.upper()}**: {', '.join(v) if isinstance(v, list) else v}")

# ================= PAGE 8: ROADMAP =================
elif current_page == "roadmap":
    st.title("🗺️ The Golden Order Sequence")
    st.caption("The mathematically verified order for creating and aligning Indian identity documents.")

    st.markdown("""
    ### 1. Anchor Proof: 10th Certificate or Birth Certificate
    - Contains your exact full name and verified Date of Birth.
    - Treat this as the permanent anchor for all government records.

    ### 2. Aadhaar Card
    - Align your demographic name and birth date with your Anchor Proof.
    - Never accept single-word names if your 10th marksheet lists a surname.

    ### 3. PAN Card
    - Apply using your updated Aadhaar e-KYC.
    - Name and DoB must match Aadhaar to allow seamless linking without late fee penalties.

    ### 4. Passport Application
    - Apply only after Aadhaar and PAN match your 10th certificate.
    - Prevents file holds, adverse police verification reports, and impounding notices.
    """)

# ================= PAGE 9: FAQS =================
elif current_page == "faqs":
    st.title("❓ Frequently Asked Questions")
    st.caption("Official clarifications from UIDAI, Income Tax Department, and Passport Office.")

    faqs = query_db("SELECT * FROM faqs ORDER BY id")
    for faq in faqs:
        with st.expander(f"📌 {faq['question']}"):
            st.write(faq['answer'])
            if faq.get("tags"):
                st.caption(f"Tags: {faq['tags']}")
