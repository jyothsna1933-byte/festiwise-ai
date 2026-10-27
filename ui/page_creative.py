"""Creative Studio (Themes, Decor, Invitations & Games) page for FestiWise AI."""

import streamlit as st
from database.db import get_full_event, save_full_event
from ui.components import render_active_event_pill, render_empty_state


def render_creative_studio():
    """Render creative concept generator, invitation wording, games, and eco-friendly tips."""
    st.markdown("### 🎨 Creative Studio")
    st.markdown("Personalized themes, color palettes, original invitation wording, menu concepts, and zero-waste alternatives.")

    active_id = st.session_state.get("active_event_id")
    if not active_id:
        render_empty_state(
            title="No Active Celebration Selected",
            message="Please select or create an event to access the Creative Studio.",
            action_page="Create Event",
            action_label="Plan Celebration"
        )
        return

    event = get_full_event(active_id)
    if not event:
        st.warning("Could not load active event.")
        return

    render_active_event_pill(event)

    creative = event.creative

    tab_theme, tab_invite, tab_menu, tab_games, tab_eco = st.tabs([
        "🎭 Theme & Decor Concepts",
        "💌 Invitation Copywriter",
        "🍽️ Menu & Drink Pairings",
        "🎲 Activities, Games & Music",
        "🌿 Sustainable & Low-Waste Ideas"
    ])

    with tab_theme:
        st.markdown(f"#### Recommended Theme: {creative.recommended_theme}")
        st.info(f"**Rationale:** {creative.theme_rationale}")

        st.markdown("##### 🎨 Color Palette")
        col_colors = st.columns(len(creative.color_palette) if creative.color_palette else 4)
        for i, color in enumerate(creative.color_palette):
            with col_colors[i]:
                st.markdown(f"""
                <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 14px; text-align: center;">
                    <div style="font-weight: 700; color: #1E293B;">{color}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("##### 🏮 Signature Decoration Concepts")
        for idx, concept in enumerate(creative.decor_concepts):
            st.markdown(f"""
            <div class="saas-card" style="padding: 16px; margin-bottom: 10px;">
                <strong style="color: #0F172A;">Concept #{idx+1}</strong>
                <p style="margin: 4px 0 0 0; color: #475569; font-size: 0.92rem;">{concept}</p>
            </div>
            """, unsafe_allow_html=True)

        with st.expander("✏️ Customize Theme & Decor"):
            new_theme = st.text_input("Theme Title", value=creative.recommended_theme)
            new_rat = st.text_area("Theme Rationale", value=creative.theme_rationale)
            if st.button("Save Theme Customizations", type="primary"):
                event.creative.recommended_theme = new_theme
                event.creative.theme_rationale = new_rat
                save_full_event(event)
                st.success("Theme details updated!")
                st.rerun()

    with tab_invite:
        st.markdown("#### 💌 Original Invitation Copy")
        st.caption("Crafted specifically for this event's tone, guest count, and cultural context:")

        st.markdown(f"""
        <div class="saas-card" style="background: #FFFDF9; border: 1px solid #FCD34D; font-family: Georgia, serif; line-height: 1.8; padding: 28px; font-size: 1.05rem; color: #1E293B;">
            {creative.invitation_wording.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Copy to Clipboard / Message Format:**")
        st.code(creative.invitation_wording, language="text")

        with st.expander("✏️ Edit Invitation Text"):
            custom_invite = st.text_area("Customized Invitation Copy", value=creative.invitation_wording, height=140)
            if st.button("Save Customized Invitation", type="primary"):
                event.creative.invitation_wording = custom_invite
                save_full_event(event)
                st.success("Invitation copy saved!")
                st.rerun()

    with tab_menu:
        st.markdown("#### 🍽️ Curated Menu & Beverage Suggestions")
        st.caption(f"Reflecting preference: **{event.input_details.food_preference}**")

        for idx, item in enumerate(creative.menu_suggestions):
            st.markdown(f"- 🍴 **Item {idx+1}:** {item}")

    with tab_games:
        st.markdown("#### 🎲 Activities, Games & Entertainment")
        col_act, col_mus = st.columns(2)
        with col_act:
            st.markdown("##### Audience Activities & Games")
            for a in creative.activities_and_games:
                st.markdown(f"- 🎯 {a}")
        with col_mus:
            st.markdown("##### Music & Performance Vibes")
            for m in creative.music_entertainment:
                st.markdown(f"- 🎵 {m}")

    with tab_eco:
        st.markdown("#### 🌿 Sustainable & Low-Waste Planning Ideas")
        st.caption("Practical ideas to minimize ecological footprint and food waste without compromising celebration flair:")

        for tip in creative.eco_friendly_tips:
            st.markdown(f"""
            <div class="saas-card" style="border-left: 4px solid #10B981; padding: 14px 18px; margin-bottom: 8px;">
                🌱 <span style="color: #065F46; font-weight: 600;">{tip}</span>
            </div>
            """, unsafe_allow_html=True)
