import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

# ── Safe API call helper ───────────────────────────────────────────────────────
def safe_post(url, **kwargs):
    """Returns (status_code, json_data, error_message)."""
    try:
        res = requests.post(url, **kwargs, timeout=5)
        try:
            return res.status_code, res.json(), None
        except requests.exceptions.JSONDecodeError:
            return res.status_code, {}, f"Server returned invalid response (status {res.status_code})"
    except requests.exceptions.ConnectionError:
        return 0, {}, "❌ Cannot connect to backend. Make sure FastAPI is running:\n`uvicorn backend.main:app --reload`"
    except requests.exceptions.Timeout:
        return 0, {}, "❌ Request timed out. Is the backend running?"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title=" RAG RBAC Chatbot", layout="centered")

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* dark card container */
.block-container {
    max-width: 480px;
    padding-top: 3rem;
}

/* role badge colours */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.badge-engineering { background:#dbeafe; color:#1e40af; }
.badge-finance     { background:#fef3c7; color:#92400e; }
.badge-general     { background:#f1f5f9; color:#475569; }
.badge-hr          { background:#fce7f3; color:#9d174d; }
.badge-marketing   { background:#dcfce7; color:#166534; }

/* sidebar clean */
section[data-testid="stSidebar"] { background: #0f172a; }
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [("token", None), ("role", None), ("username", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar nav ───────────────────────────────────────────────────────────────
if not st.session_state.token:
    menu = st.sidebar.radio("Navigation", ["🔑 Login", "📝 Register"], label_visibility="collapsed")
else:
    st.sidebar.markdown(f"### 👤 {st.session_state.username}")
    badge_cls = f"badge-{st.session_state.role}"
    st.sidebar.markdown(
        f'<span class="badge {badge_cls}">{st.session_state.role}</span>',
        unsafe_allow_html=True,
    )
    st.sidebar.divider()
    if st.sidebar.button("Logout", use_container_width=True):
        requests.post(f"{API_URL}/logout", params={"token": st.session_state.token})
        st.session_state.token = None
        st.session_state.role = None
        st.session_state.username = None
        st.rerun()
    menu = None

# ── REGISTER ──────────────────────────────────────────────────────────────────
if menu == "📝 Register":
    st.title("Create account")
    st.caption("Fill in the details below to get started.")
    st.divider()

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.selectbox(
        "Department / Role",
        ["engineering", "finance", "general", "hr", "marketing"],
        help="Select the department this account belongs to.",
    )

    st.markdown("""
    | Department | Access |
    |------------|--------|
    | 🛠️ engineering | Technical tools & systems |
    | 💰 finance | Financial reports & data |
    | 🏢 general | General company resources |
    | 👥 hr | People & HR management |
    | 📣 marketing | Campaigns & content |
    """)

    st.divider()
    if st.button("Register →", use_container_width=True, type="primary"):
        if not username or not password:
            st.warning("Please fill in all fields.")
        else:
            status, data, err = safe_post(f"{API_URL}/register", json={
                "username": username,
                "password": password,
                "role": role,
            })
            if err:
                st.error(err)
            elif status == 200:
                st.success(f"Account created! Role assigned: **{data['role']}**. Please log in.")
            else:
                st.error(data.get("detail", "Registration failed."))

# ── LOGIN ─────────────────────────────────────────────────────────────────────
elif menu == "🔑 Login":
    st.title("Welcome back")
    st.caption("Sign in to access your dashboard.")
    st.divider()

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    st.divider()
    if st.button("Login →", use_container_width=True, type="primary"):
        if not username or not password:
            st.warning("Please fill in all fields.")
        else:
            status, data, err = safe_post(f"{API_URL}/login", json={
                "username": username,
                "password": password,
            })
            if err:
                st.error(err)
            elif status == 200:
                st.session_state.token = data["token"]
                st.session_state.role = data["role"]
                st.session_state.username = data["username"]
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error(data.get("detail", "Login failed."))

# ── DASHBOARD (post-login, department-based) ─────────────────────────────────
if st.session_state.token:
    role = st.session_state.role

    st.title("Dashboard")
    badge_cls = f"badge-{role}"
    st.markdown(
        f'Logged in as <b>{st.session_state.username}</b> &nbsp;'
        f'<span class="badge {badge_cls}">{role}</span>',
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Chatbot — visible to all ───────────────────────────────────────────
    st.subheader("💬 Chatbot")
    user_input = st.text_input("Ask something")
    if st.button("Send", type="primary"):
        st.info(f"Echo: {user_input}")  # replace with real LLM call

    st.divider()

    # ── Department-specific panels ─────────────────────────────────────────
    if role == "engineering":
        st.subheader("🛠️ Engineering Tools")
        st.info("CI/CD pipelines, system health, incident tracker, and technical docs.")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Open PRs", "—")
        with col2:
            st.metric("Build Status", "—")

    elif role == "finance":
        st.subheader("💰 Finance Dashboard")
        st.info("Budget reports, expense approvals, and financial forecasts.")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Monthly Budget", "—")
        with col2:
            st.metric("Pending Approvals", "—")

    elif role == "hr":
        st.subheader("👥 HR Portal")
        st.info("Employee records, leave management, and onboarding checklists.")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Headcount", "—")
        with col2:
            st.metric("Open Positions", "—")

    elif role == "marketing":
        st.subheader("📣 Marketing Hub")
        st.info("Campaign manager, content calendar, and analytics.")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Active Campaigns", "—")
        with col2:
            st.metric("Leads This Month", "—")

    elif role == "general":
        st.subheader("🏢 General Resources")
        st.info("Company announcements, shared docs, and help desk.")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Announcements", "—")
        with col2:
            st.metric("Open Tickets", "—")