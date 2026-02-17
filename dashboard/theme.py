"""
Design System Theme Adapter
Instantiated from: .agent/skills/secure-ux-design/SKILL.md

This module interprets the Universal Design Principles into CSS compatible with 
Streamlit (and web views). Use `apply_theme()` in your dashboard app.
"""

import streamlit as st

# ==============================================================================
# SECTION 1: DESIGN TOKENS (Pattern: Design System Foundation)
# ==============================================================================

# HSL Color System
COLORS = {
    'primary': 'hsl(220, 70%, 50%)',     # Base Blue
    'primary_light': 'hsl(220, 70%, 95%)',
    'success': 'hsl(142, 71%, 45%)',     # Green
    'warning': 'hsl(38, 92%, 50%)',      # Orange
    'error': 'hsl(0, 72%, 51%)',         # Red
    'text': '#1a1a1a',
    'background': '#ffffff',
    'gray_100': '#f3f4f6',
    'gray_200': '#e5e7eb',
}

# Spacing Scale
SPACING = {
    'sm': '0.5rem',  # 8px
    'md': '1rem',    # 16px
    'lg': '1.5rem',  # 24px
    'xl': '2rem',    # 32px
}

# ==============================================================================
# SECTION 2: CSS INJECTION (Pattern: Universal UI)
# ==============================================================================

def get_base_css():
    """Returns the CSS string defining the design system variables and global styles."""
    return f"""
    <style>
        :root {{
            --primary: {COLORS['primary']};
            --primary-light: {COLORS['primary_light']};
            --success: {COLORS['success']};
            --warning: {COLORS['warning']};
            --error: {COLORS['error']};
            --text-main: {COLORS['text']};
            --space-md: {SPACING['md']};
            --radius-md: 8px;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
        }}

        /* Typography & Accessibility */
        body {{
            font-family: 'Inter', sans-serif;
            color: var(--text-main);
        }}

        /* Component: Metric Card */
        .metric-card {{
            background: white;
            padding: var(--space-md);
            border-radius: var(--radius-md);
            border: 1px solid {COLORS['gray_200']};
            box-shadow: var(--shadow-sm);
            margin-bottom: var(--space-md);
            transition: transform 0.2s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }}

        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary);
        }}

        .metric-label {{
            font-size: 0.875rem;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        /* Status Indicators */
        .status-badge {{
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        
        .status-active {{ background: {COLORS['success']}; color: white; }}
        .status-error {{ background: {COLORS['error']}; color: white; }}
        .status-warning {{ background: {COLORS['warning']}; color: black; }}

    </style>
    """

def apply_theme():
    """Injects the design system CSS into the Streamlit app."""
    st.markdown(get_base_css(), unsafe_allow_html=True)

# ==============================================================================
# SECTION 3: COMPONENT HELPERS (Pattern: Domain Specific UI)
# ==============================================================================

def render_metric_card(label: str, value: str, subtext: str = None):
    """Renders a styled metric card using HTML."""
    html = f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {f'<div style="font-size: 0.8em; color: gray;">{subtext}</div>' if subtext else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_status(status: str):
    """Renders a status badge (active/error/warning)."""
    status_map = {
        'active': 'status-active',
        'online': 'status-active',
        'error': 'status-error',
        'offline': 'status-error',
        'warning': 'status-warning'
    }
    cls = status_map.get(status.lower(), 'status-warning')
    st.markdown(f'<span class="status-badge {cls}">{status.upper()}</span>', unsafe_allow_html=True)
