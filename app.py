import streamlit as st
import random
from datetime import datetime, time, timedelta

from search_engine import search_session_history
from main import (
    create_player,
    calculate_sustainability_score,
    apply_session_effects,
    check_burnout_risk,
    display_comparison,
    generate_session_data,
    save_sessions,
    session_log,
)
from models import LevelHeadedDB


# Initialize session state to preserve player data across reruns (backed by JSON DB)
if "db" not in st.session_state:
    st.session_state.db = LevelHeadedDB("levelheaded_db.json")
    data = st.session_state.db.load()
    st.session_state.player = data["player"]
    st.session_state.session_log = data["session_log"]
    st.session_state.days_simulated = data["days_simulated"]


def calculate_focus_score(player):
    """Calculate focus score from sleep, stress, and motivation."""
    focus_score = max(0, min(100, round(
        (player["sleep_hours"] / 8.0) * 40 +
        ((100 - player["stress_level"]) / 100.0) * 30 +
        (player["motivation"] / 100.0) * 30
    )))
    player["focus_score"] = focus_score
    return focus_score


def main():
    st.set_page_config(
        page_title="LevelHeaded - Sustainable Gaming Simulator",
        page_icon="🎮",
        layout="wide"
    )
    
    st.title("🎮 LevelHeaded - Sustainable Gaming Simulator")
    st.markdown("**Track your gaming habits and discover the hidden costs of excessive play. Build sustainable habits for long-term success.**")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Go to",
            ["🏠 Dashboard", "📅 End of Day Reflection", "🔍 Search Session History", "📊 Session Scanner"]
        )
        
        st.divider()
        st.header("Quick Actions")
        if st.button("💾 Save to JSON DB", use_container_width=True):
            db = st.session_state.db
            db.save_player(st.session_state.player)
            db.set_days_simulated(st.session_state.days_simulated)
            data = db.load()
            data["session_log"] = st.session_state.session_log
            db.save(data)
            st.success("Saved to levelheaded_db.json!")
        if st.button("🔄 Reset All Data", use_container_width=True):
            data = st.session_state.db.reset()
            st.session_state.player = data["player"]
            st.session_state.session_log = data["session_log"]
            st.session_state.days_simulated = data["days_simulated"]
            st.success("Data reset!")
            st.rerun()
    
    player = st.session_state.player
    
    if page == "🏠 Dashboard":
        st.header("Player Status Dashboard")
        
        focus_score = calculate_focus_score(player)
        sustainability = calculate_sustainability_score(player)
        
        # Display core metrics using st.metric
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Skill Level", player["skill_level"])
            st.metric("Stress Level", player["stress_level"], 
                     delta=f"{player['stress_level'] - 20}" if st.session_state.days_simulated > 0 else None)
        with col2:
            st.metric("Sleep Hours", f"{player['sleep_hours']} hrs")
            st.metric("Motivation", player["motivation"])
        with col3:
            st.metric("Personal Growth Time", f"{player['personal_growth_time']} hrs")
            st.metric("Focus Score", focus_score)
        with col4:
            st.metric("Today's Play Time", f"{player['hours_played_today']} hrs")
            st.metric("Sustainability Score", f"{sustainability}/100")
        
        st.divider()
        
        # Burnout risk
        burnout = check_burnout_risk(player)
        if "HIGH" in burnout:
            st.error(f"⚠️ {burnout}")
        elif "MODERATE" in burnout or "WARNING" in burnout:
            st.warning(f"⚠️ {burnout}")
        elif "NEGLECT" in burnout:
            st.warning(f"⚠️ {burnout}")
        else:
            st.success(f"✅ {burnout}")
        
        # Focus warning
        if focus_score < 40:
            st.error("WARNING: Your focus has collapsed. Continuing to play will lead to costly in-game mistakes and tilted decisions.")
        
        # Display days simulated
        st.info(f"Days Simulated: {st.session_state.days_simulated}")
    
    elif page == "📅 End of Day Reflection":
        st.header("End of Day - Reflect on your day")
        st.markdown("Log what you actually did today, not what you planned to do.")
        
        with st.form("end_of_day_form"):
            hours_played = st.number_input(
                "How many hours did you play today? (0-12)",
                min_value=0.0,
                max_value=12.0,
                step=0.5,
                value=0.0
            )
            
            st.subheader("Sleep Schedule")
            col_sleep1, col_sleep2 = st.columns(2)
            with col_sleep1:
                wake_up_time = st.time_input("Wake up time", value=time(8, 0))
            with col_sleep2:
                bedtime = st.time_input("Bedtime / Sleep time", value=time(23, 0))
            
            # Compute sleep hours from schedule (handles midnight crossover)
            wake_dt = datetime.combine(datetime.today(), wake_up_time)
            bed_dt = datetime.combine(datetime.today(), bedtime)
            if wake_dt <= bed_dt:
                wake_dt += timedelta(days=1)
            scheduled_sleep_hours = max(0.0, min(12.0, (wake_dt - bed_dt).total_seconds() / 3600.0))
            st.caption(f"Scheduled sleep: {scheduled_sleep_hours:.1f} hours")
            
            st.subheader("Did you do any of these today?")
            col1, col2, col3 = st.columns(3)
            with col1:
                exercised = st.checkbox("Did you exercise today?")
            with col2:
                socialized = st.checkbox("Did you socialize with friends/family?")
            with col3:
                learned = st.checkbox("Did you learn something new (study/skill)?")
            
            submitted = st.form_submit_button("Log Day & See Impact", use_container_width=True)
            
            if submitted:
                # Apply sleeping schedule to player's sleep hours first
                player["sleep_hours"] = scheduled_sleep_hours
                
                # Apply effects
                apply_session_effects(player, hours_played, exercised, socialized, learned)
                st.session_state.days_simulated += 1
                
                # Sleep hours come from the user's schedule, not gaming subtraction
                player["sleep_hours"] = scheduled_sleep_hours
                
                # Log session
                day_number = len(st.session_state.session_log) + 1
                session_code = (
                    f"SES-{day_number:03d}-{int(hours_played)}H-ST{int(player['stress_level'])}"
                    f"-MT{int(player['motivation'])}-SL{int(round(player['sleep_hours']))}"
                )
                st.session_state.session_log.append(session_code)
                
                # Persist to JSON DB instantly so data survives a page refresh
                db = st.session_state.db
                db.save_player(player)
                db.log_session(session_code)
                db.set_days_simulated(st.session_state.days_simulated)
                
                st.success("Day logged successfully!")
                
                # Show comparison
                st.subheader("Impact Analysis")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### PERCEIVED GAINS (What players think they get)")
                    gains_shown = False
                    if hours_played > 0:
                        if hours_played > 5:
                            st.write(f"• +{round(hours_played * 1.5, 1)} Skill points (heavy grind)")
                            gains_shown = True
                        elif hours_played > 3:
                            st.write(f"• +{round(hours_played, 1)} Skill points")
                            gains_shown = True
                        else:
                            st.write(f"• +{round(hours_played * 0.5, 1)} Skill points (light practice)")
                            gains_shown = True
                    if exercised:
                        st.write("• +5 Motivation (feeling healthy)")
                        gains_shown = True
                    if socialized:
                        st.write("• +3 Motivation (connected)")
                        gains_shown = True
                    if learned:
                        st.write("• +2 Skill Level (+5 Motivation)")
                        gains_shown = True
                    if not gains_shown:
                        st.write("• No major gains today")
                
                with col2:
                    st.markdown("### HIDDEN COSTS (What accumulates behind the scenes)")
                    costs_shown = False
                    if hours_played > 0:
                        if hours_played > 5:
                            st.write("• +15 Stress (overtraining)")
                            st.write("• -1.5 Sleep hours")
                            st.write("• -5 Motivation")
                            costs_shown = True
                        elif hours_played > 3:
                            st.write("• +8 Stress")
                            st.write("• -0.5 Sleep hours")
                            costs_shown = True
                    if exercised:
                        st.write("• -1.0 Personal Growth Time")
                        costs_shown = True
                    if socialized:
                        st.write("• -1.0 Personal Growth Time")
                        costs_shown = True
                    if learned:
                        st.write("• -1.5 Personal Growth Time")
                        costs_shown = True
                    if player["sleep_hours"] < 6:
                        st.write(f"• REDUCED Focus and Reaction Time (sleep: {player['sleep_hours']} hrs)")
                        costs_shown = True
                    if not costs_shown:
                        st.write("• Minimal costs today")
                    
                    if player["personal_growth_time"] == 0:
                        st.error("*** WARNING: Personal Growth Time has reached zero. Important life goals, education, and relationships are being neglected. ***")
                
                st.divider()
                burnout = check_burnout_risk(player)
                if "HIGH" in burnout:
                    st.error(f"⚠️ {burnout}")
                elif "MODERATE" in burnout or "WARNING" in burnout or "NEGLECT" in burnout:
                    st.warning(f"⚠️ {burnout}")
                else:
                    st.success(f"✅ {burnout}")
    
    elif page == "🔍 Search Session History":
        st.header("Search Session History")
        st.markdown("Search through your session history by player name, team, department, or session code.")
        
        query = st.text_input("Enter search term", placeholder="e.g., Taylor, Alpha, SES-001")
        
        if st.button("Search", use_container_width=True):
            if query.strip():
                with st.spinner("Searching..."):
                    try:
                        # Run the full search pipeline and render results in UI (no terminal dump)
                        from nested_v1 import load_session_history
                        from search_engine import (
                            build_multi_layered_dataset,
                            flatten_sessions,
                            search_sessions,
                            classify_risk,
                        )
                        
                        session_codes = load_session_history()
                        if not session_codes:
                            st.warning("No session data available. Log some days first!")
                        else:
                            dataset = build_multi_layered_dataset(session_codes)
                            flat_sessions = flatten_sessions(dataset)
                            results = search_sessions(flat_sessions, query.strip())
                            
                            st.success(f"Found {len(results)} match(es) for '{query.strip()}'.")
                            
                            if results:
                                # Display summary metrics
                                avg_hours = sum(r["hours_played"] for r in results) / len(results)
                                avg_stress = sum(r["stress_level"] for r in results) / len(results)
                                avg_motivation = sum(r["motivation"] for r in results) / len(results)
                                avg_sleep = sum(r["sleep_hours"] for r in results) / len(results)
                                
                                col1, col2, col3, col4 = st.columns(4)
                                col1.metric("Avg Hours Played", f"{avg_hours:.1f}")
                                col2.metric("Avg Stress Level", f"{avg_stress:.1f}")
                                col3.metric("Avg Motivation", f"{avg_motivation:.1f}")
                                col4.metric("Avg Sleep Hours", f"{avg_sleep:.1f}")
                                
                                # Risk counts
                                risk_counts = {"AT RISK": 0, "MODERATE": 0, "HEALTHY": 0}
                                for r in results:
                                    risk_counts[classify_risk(r["hours_played"])] += 1
                                
                                col5, col6, col7 = st.columns(3)
                                col5.metric("AT RISK (>5h)", risk_counts["AT RISK"])
                                col6.metric("MODERATE (>3h)", risk_counts["MODERATE"])
                                col7.metric("HEALTHY", risk_counts["HEALTHY"])
                                
                                st.divider()
                                st.subheader("Search Results")
                                
                                # Build table rows
                                table_rows = []
                                for r in results[:20]:
                                    table_rows.append({
                                        "Dept": r["department"],
                                        "Team": r["team"],
                                        "Player": f"{r['player_id']} - {r['player_name']}",
                                        "Session": r["session_code"],
                                        "Hours Played": r["hours_played"],
                                        "Risk": classify_risk(r["hours_played"]),
                                        "Stress Level": r["stress_level"],
                                        "Motivation": r["motivation"],
                                        "Sleep Hours": r["sleep_hours"],
                                    })
                                
                                st.dataframe(table_rows, use_container_width=True, hide_index=True)
                                
                                if len(results) > 20:
                                    st.info(f"Showing first 20 of {len(results)} results.")
                            else:
                                st.info(f"No matches found for '{query.strip()}'.")
                    except Exception as e:
                        st.error(f"Search error: {e}")
            else:
                st.warning("Please enter a search term.")
    
    elif page == "📊 Session Scanner":
        st.header("Session Code Scanner")
        st.markdown("Read and analyze session codes from session_data.txt with the expert 5-hour threshold.")
        
        if st.button("Scan Sessions", use_container_width=True):
            from sequence_logic import parse_session_code, validate_code_format
            
            # Read from JSON DB first, fall back to session_data.txt
            codes = st.session_state.get("session_log", [])
            if not codes:
                try:
                    with open("session_data.txt", "r") as file:
                        lines = file.readlines()
                    codes = [l.strip() for l in lines if l.strip()]
                except Exception:
                    codes = []
            else:
                lines = [c + "\n" for c in codes]
                
                if not codes:
                    st.warning("No session data available. Log some days first!")
                    return
                
                st.subheader(f"Found {len(codes)} session(s)")
                
                for code in codes:
                    session_code = code.strip()
                    if not session_code:
                        continue
                    
                    if not validate_code_format(session_code):
                        st.warning(f"Invalid code format: {session_code}")
                        continue
                    
                    try:
                        session_data = parse_session_code(session_code)
                        with st.expander(f"Session {session_data['session_id']}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Hours Played", session_data['hours_played'])
                                st.metric("Stress Level", session_data['stress_level'])
                            with col2:
                                st.metric("Motivation", session_data['motivation'])
                                st.metric("Sleep Hours", session_data['sleep_hours'])
                            
                            if session_data["hours_played"] > 5:
                                st.error("⚠️ WARNING: Take a break! Excessive gaming detected.")
                            else:
                                st.success("✅ Gaming time is within the set limit.")
                    except Exception as e:
                        st.warning(f"Could not parse: {session_code} - {e}")


if __name__ == "__main__":
    main()
