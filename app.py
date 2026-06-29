import streamlit as st
import pandas as pd
from datetime import datetime
from core.memory import (
    init_db, save_history, load_history, clear_history,
    get_action_logs, get_error_logs, get_stats
)
from core.orchestrator import Orchestrator

st.set_page_config(
    page_title = "Multi-Agent Assistant",
    page_icon  = "🤖",
    layout     = "wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

.metric-card {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
}
.metric-value {
    font-size: 28px;
    font-weight: 700;
    color: #1a1a2e;
}
.metric-label {
    font-size: 12px;
    color: #666;
    margin-top: 2px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.status-success {
    background:#d4edda; color:#155724;
    padding:2px 8px; border-radius:10px;
    font-size:11px; font-weight:600;
}
.status-error {
    background:#f8d7da; color:#721c24;
    padding:2px 8px; border-radius:10px;
    font-size:11px; font-weight:600;
}
.status-resolved {
    background:#cce5ff; color:#004085;
    padding:2px 8px; border-radius:10px;
    font-size:11px; font-weight:600;
}
.provider-badge {
    background:#e9ecef; color:#495057;
    padding:2px 8px; border-radius:10px;
    font-size:11px;
}
</style>
Note: Gmail/Calendar tools can only be used after authenticating with your own API keys. Developer keys have been restricted to prevent exposure of personal data.
For setup instructions, please refer to <b>README.md</b>.
""", unsafe_allow_html=True)

# ── Agent metadata ─────────────────────────────────────────────────────────────
AGENT_META = {
    "auto":     {"icon": "✨", "label": "Auto-Route",  "color": "#7F77DD"},
    "email":    {"icon": "📧", "label": "Email",       "color": "#185FA5"},
    "research": {"icon": "🔍", "label": "Research",    "color": "#534AB7"},
    "calendar": {"icon": "📅", "label": "Calendar",    "color": "#3B6D11"},
    "travel":   {"icon": "✈️", "label": "Travel",      "color": "#854F0B"},
}

# ── Init ───────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_orchestrator():
    init_db()
    orch = Orchestrator()
    for name, agent in orch.agents.items():
        agent.history = load_history(name)
    return orch

def get_agent_key(orch, agent) -> str:
    return next((k for k, v in orch.agents.items() if v == agent), "research")

orch = get_orchestrator()

# ── Top navigation ─────────────────────────────────────────────────────────────
tab_chat, tab_logs = st.tabs(["💬  Chat", "📊  Logs Dashboard"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CHAT
# ══════════════════════════════════════════════════════════════════════════════
with tab_chat:
    col_sidebar, col_main = st.columns([1, 3])

    with col_sidebar:
        st.markdown("### 🤖 Agents")
        mode = st.radio(
            label            = "Agent",
            options          = ["auto", "email", "research", "calendar", "travel"],
            format_func      = lambda x: f"{AGENT_META[x]['icon']}  {AGENT_META[x]['label']}",
            label_visibility = "collapsed",
        )
        st.markdown("---")

        if mode != "auto":
            agent = orch.agents[mode]
            st.caption(f"🔧 **Provider:** {agent.provider}")
            st.caption(f"💬 **Memory:** {len(agent.history)} messages")
            if st.button("🗑️ Clear memory", use_container_width=True):
                agent.reset()
                clear_history(mode)
                st.session_state[f"messages_{mode}"] = []
                st.rerun()
        else:
            st.caption("Gemini 2.5 Flash routes to the best agent automatically.")

        st.markdown("---")
        st.markdown("**📖 Tips:**")
        st.markdown("- Type anything in Auto mode")
        st.markdown("- Responses stream in real time ⚡")
        st.markdown("- Gmail/Calendar open browser on first use")
        st.markdown("- Errors auto-fallback to backup provider")
        st.markdown("- Check **Logs Dashboard** tab for details")

    with col_main:
        meta = AGENT_META[mode]
        if mode == "auto":
            st.markdown(f"## {meta['icon']} Auto-Route Mode")
            st.caption("Gemini 2.5 Flash picks the best agent for every message.")
        else:
            agent = orch.agents[mode]
            st.markdown(f"## {meta['icon']} {agent.name}")
            st.caption(f"Provider: **{agent.provider}**  •  Streams in real time ⚡  •  Auto-fallback on errors 🛡️")

        st.markdown("---")

        session_key = f"messages_{mode}"
        if session_key not in st.session_state:
            st.session_state[session_key] = []

        # ── Scroll-to-bottom JS — runs every render ───────────────────────────
        st.markdown("""
        <script>
        function scrollToBottom() {
            const chatContainer = window.parent.document.querySelector(
                '[data-testid="stChatMessageContainer"]'
            );
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            // Also scroll the main block container
            const main = window.parent.document.querySelector(
                'section[data-testid="stMain"]'
            );
            if (main) main.scrollTop = main.scrollHeight;

            window.parent.scrollTo(0, window.parent.document.body.scrollHeight);
        }
        // Run immediately and after a short delay to catch late renders
        scrollToBottom();
        setTimeout(scrollToBottom, 300);
        setTimeout(scrollToBottom, 700);
        </script>
        """, unsafe_allow_html=True)

        # Render chat history
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state[session_key]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Chat input — always rendered at the bottom by Streamlit
        if prompt := st.chat_input("Type your message..."):

            # Save user message and rerun so it appears before we stream
            st.session_state[session_key].append({"role": "user", "content": prompt})
            st.session_state["_pending_prompt"] = prompt
            st.session_state["_pending_mode"]   = mode
            st.rerun()

        # ── Process pending prompt (after rerun, input is now at bottom) ──────
        if st.session_state.get("_pending_prompt") and \
           st.session_state.get("_pending_mode") == mode:

            prompt = st.session_state.pop("_pending_prompt")
            st.session_state.pop("_pending_mode", None)

            with chat_container:
                with st.chat_message("assistant"):
                    placeholder = st.empty()
                    streamed    = ""
                    agent_label = ""

                    try:
                        if mode == "auto":
                            with st.spinner("🧭 Routing to best agent..."):
                                detected_name, reason = orch.detect_agent(prompt)
                                if detected_name not in orch.agents:
                                    detected_name = "research"
                                active_agent = orch.agents[detected_name]
                                key          = detected_name
                                agent_label  = (
                                    f"*{AGENT_META[detected_name]['icon']} "
                                    f"Routed to **{active_agent.name}** — {reason}*\n\n"
                                )
                                placeholder.markdown(agent_label + "▋")
                        else:
                            active_agent = orch.agents[mode]
                            key          = mode

                        for token in active_agent.chat_stream(prompt):
                            streamed    += token
                            placeholder.markdown(agent_label + streamed + "▋")

                        placeholder.markdown(agent_label + streamed)
                        save_history(key, active_agent.history)
                        st.session_state[session_key].append({
                            "role": "assistant", "content": agent_label + streamed
                        })

                    except FileNotFoundError as e:
                        err = f"❌ **Setup required:** {str(e)}"
                        placeholder.error(err)
                        st.session_state[session_key].append({"role": "assistant", "content": err})

                    except Exception as e:
                        err = f"⚠️ **Unexpected error:** {str(e)}"
                        placeholder.error(err)
                        st.session_state[session_key].append({"role": "assistant", "content": err})

            # Rerun one final time so the input box re-anchors below all messages
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — LOGS DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab_logs:
    st.markdown("## 📊 Logs Dashboard")
    st.caption("Real-time view of all agent actions, errors, and system health.")

    # Refresh button
    col_r1, col_r2 = st.columns([5, 1])
    with col_r2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # ── Stats row ─────────────────────────────────────────────────────────────
    stats = get_stats()

    total_actions  = sum(stats.get("actions_per_agent", {}).values())
    total_errors   = stats.get("total_errors", 0)
    resolved       = stats.get("resolved_errors", 0)
    total_messages = sum(stats.get("messages_per_agent", {}).values())
    success_count  = stats.get("status_counts", {}).get("success", 0)
    error_count    = stats.get("status_counts", {}).get("error", 0)
    success_rate   = (
        f"{round(success_count / total_actions * 100)}%"
        if total_actions > 0 else "N/A"
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_actions}</div>
            <div class="metric-label">Total Actions</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{success_rate}</div>
            <div class="metric-label">Success Rate</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_errors}</div>
            <div class="metric-label">Total Errors</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:#28a745">{resolved}</div>
            <div class="metric-label">Auto-Resolved</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_messages}</div>
            <div class="metric-label">Total Messages</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Agent activity bar chart ───────────────────────────────────────────────
    actions_data = stats.get("actions_per_agent", {})
    msg_data     = stats.get("messages_per_agent", {})

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("#### ⚡ Actions per Agent")
        if actions_data:
            df_actions = pd.DataFrame(
                list(actions_data.items()), columns=["Agent", "Actions"]
            ).sort_values("Actions", ascending=False)
            st.bar_chart(df_actions.set_index("Agent"), color="#7F77DD")
        else:
            st.info("No actions logged yet. Start chatting!")

    with col_chart2:
        st.markdown("#### 💬 Conversation Length per Agent")
        if msg_data:
            df_msgs = pd.DataFrame(
                list(msg_data.items()), columns=["Agent", "Messages"]
            ).sort_values("Messages", ascending=False)
            st.bar_chart(df_msgs.set_index("Agent"), color="#185FA5")
        else:
            st.info("No conversations yet.")

    st.markdown("---")

    # ── Action log table ──────────────────────────────────────────────────────
    st.markdown("#### 📋 Action Log")

    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        agent_filter = st.selectbox(
            "Filter by agent",
            ["all", "email", "research", "calendar", "travel"],
            label_visibility="collapsed",
        )
    with col_f2:
        log_limit = st.selectbox(
            "Rows", [25, 50, 100], label_visibility="collapsed"
        )

    action_logs = get_action_logs(
        agent=agent_filter if agent_filter != "all" else None,
        limit=log_limit
    )

    if action_logs:
        rows = []
        for log in action_logs:
            status_html = (
                f'<span class="status-success">✅ success</span>'
                if log["status"] == "success"
                else f'<span class="status-error">❌ error</span>'
            )
            rows.append({
                "Timestamp": log["timestamp"][:16].replace("T", " "),
                "Agent":     f"{AGENT_META.get(log['agent'], {}).get('icon', '🤖')} {log['agent']}",
                "Action":    log["action"],
                "Detail":    log["detail"][:80] + ("..." if len(log["detail"]) > 80 else ""),
                "Status":    log["status"],
            })
        df = pd.DataFrame(rows)

        # Color rows by status
        def highlight_status(row):
            if row["Status"] == "error":
                return ["background-color: #fff5f5"] * len(row)
            return [""] * len(row)

        styled = df.style.apply(highlight_status, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=True)
    else:
        st.info("No actions logged yet. Start chatting to see activity here.")

    st.markdown("---")

    # ── Error log table ────────────────────────────────────────────────────────
    st.markdown("#### 🛡️ Error & Fallback Log")
    st.caption("Shows provider failures and whether the fallback resolved them automatically.")

    error_logs = get_error_logs(limit=50)

    if error_logs:
        rows = []
        for log in error_logs:
            resolved_label = "✅ Resolved" if log["resolved"] else "❌ Unresolved"
            rows.append({
                "Timestamp": log["timestamp"][:16].replace("T", " "),
                "Agent":     log["agent"],
                "Failed Provider":   log["provider"],
                "Fallback Used":     log["fallback"] if log["fallback"] else "none",
                "Resolved":          resolved_label,
                "Error":             log["error"][:70] + ("..." if len(log["error"]) > 70 else ""),
            })
        df_err = pd.DataFrame(rows)

        def highlight_resolved(row):
            if "Unresolved" in row["Resolved"]:
                return ["background-color: #fff5f5"] * len(row)
            if "Resolved" in row["Resolved"]:
                return ["background-color: #f0fff4"] * len(row)
            return [""] * len(row)

        styled_err = df_err.style.apply(highlight_resolved, axis=1)
        st.dataframe(styled_err, use_container_width=True, hide_index=True)

        # Summary
        unresolved = sum(1 for l in error_logs if not l["resolved"])
        if unresolved == 0:
            st.success(f"✅ All {len(error_logs)} errors were automatically resolved via fallback.")
        else:
            st.warning(
                f"⚠️ {unresolved} error(s) could not be auto-resolved. "
                "Check your API keys and network connection."
            )
    else:
        st.success("✅ No errors logged. All systems healthy!")

    st.markdown("---")

    # ── Clear logs section ────────────────────────────────────────────────────
    st.markdown("#### 🗑️ Manage Logs")
    col_cl1, col_cl2, col_cl3 = st.columns(3)

    with col_cl1:
        if st.button("Clear Action Logs", use_container_width=True):
            import sqlite3
            conn = sqlite3.connect("memory.db")
            conn.execute("DELETE FROM actions_log")
            conn.commit()
            conn.close()
            st.success("Action logs cleared.")
            st.rerun()

    with col_cl2:
        if st.button("Clear Error Logs", use_container_width=True):
            import sqlite3
            conn = sqlite3.connect("memory.db")
            conn.execute("DELETE FROM error_log")
            conn.commit()
            conn.close()
            st.success("Error logs cleared.")
            st.rerun()

    with col_cl3:
        if st.button("Clear All Logs", use_container_width=True, type="primary"):
            import sqlite3
            conn = sqlite3.connect("memory.db")
            conn.execute("DELETE FROM actions_log")
            conn.execute("DELETE FROM error_log")
            conn.commit()
            conn.close()
            st.success("All logs cleared.")
            st.rerun()