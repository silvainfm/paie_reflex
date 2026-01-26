"""
Design tokens for Monaco Paie - Premium Swiss minimalist aesthetic
Inspired by Stripe/Linear with blue primary palette
"""

# ============================================================================
# COLOR PALETTE
# ============================================================================

# Primary Blues (Navy → Sky gradient)
COLORS = {
    # Primary hierarchy
    "primary-950": "#0a1628",      # Deep navy - headings, strong text
    "primary-900": "#0f2439",      # Navy - primary buttons, active states
    "primary-800": "#1e3a5f",      # Dark blue - hover states
    "primary-700": "#1e4976",      # Mid-dark blue
    "primary-600": "#2563eb",      # Core blue - primary actions
    "primary-500": "#3b82f6",      # Bright blue - links, highlights
    "primary-400": "#60a5fa",      # Light blue - secondary actions
    "primary-300": "#93c5fd",      # Pale blue - backgrounds
    "primary-200": "#bfdbfe",      # Very pale - subtle fills
    "primary-100": "#dbeafe",      # Whisper blue - hover backgrounds
    "primary-50": "#eff6ff",       # Almost white - cards on blue bg

    # Neutrals (warm gray for sophistication)
    "neutral-950": "#0a0a0b",      # True black (sparingly)
    "neutral-900": "#18181b",      # Near black - main text
    "neutral-800": "#27272a",      # Dark gray - secondary text
    "neutral-700": "#3f3f46",      # Medium dark - muted text
    "neutral-600": "#52525b",      # Medium - icons
    "neutral-500": "#71717a",      # Mid gray - placeholders
    "neutral-400": "#a1a1aa",      # Light gray - labels
    "neutral-300": "#d4d4d8",      # Pale gray - borders
    "neutral-200": "#e4e4e7",      # Very pale - dividers
    "neutral-100": "#f4f4f5",      # Off white - subtle backgrounds
    "neutral-50": "#fafafa",       # Pure background
    "white": "#ffffff",            # Cards, modals

    # Status colors
    "success-600": "#16a34a",      # Green - validated
    "success-500": "#22c55e",
    "success-300": "#86efac",      # Light green - borders
    "success-100": "#dcfce7",
    "warning-600": "#ea580c",      # Orange - edge cases
    "warning-500": "#f97316",
    "warning-300": "#fdba74",      # Light orange - borders
    "warning-100": "#ffedd5",
    "error-600": "#dc2626",        # Red - errors
    "error-500": "#ef4444",
    "error-300": "#fca5a5",        # Light red - borders
    "error-200": "#fecaca",        # Very light red - hover states
    "error-100": "#fee2e2",
    "info-600": "#0284c7",         # Cyan - informational
    "info-500": "#06b6d4",
    "info-100": "#cffafe",
}

# Gradient definitions
GRADIENTS = {
    "primary": "linear-gradient(135deg, #1e4976 0%, #2563eb 100%)",
    "primary-soft": "linear-gradient(135deg, #2563eb 0%, #60a5fa 100%)",
    "subtle": "linear-gradient(180deg, #ffffff 0%, #fafafa 100%)",
    "glass": "linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(255,255,255,0.95) 100%)",
    "page-bg": "linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)",
    "card-hover": "linear-gradient(180deg, #ffffff 0%, #f4f4f5 100%)",
}

# ============================================================================
# SPACING SYSTEM (8px base grid)
# ============================================================================

SPACING = {
    "0": "0",
    "0.5": "0.125rem",    # 2px - hairline gaps
    "1": "0.25rem",       # 4px - tight spacing
    "1.5": "0.375rem",    # 6px
    "2": "0.5rem",        # 8px - base unit
    "3": "0.75rem",       # 12px - small gaps
    "4": "1rem",          # 16px - standard gap
    "5": "1.25rem",       # 20px - comfortable gap
    "6": "1.5rem",        # 24px - section spacing
    "8": "2rem",          # 32px - large spacing
    "10": "2.5rem",       # 40px - page padding
    "12": "3rem",         # 48px - major sections
    "16": "4rem",         # 64px - hero spacing
    "20": "5rem",         # 80px
}

# Component-specific spacing presets
COMPONENT_SPACING = {
    "navbar_padding": "1rem 2rem",          # 16px 24px
    "sidebar_padding": "1.5rem 1rem",       # 24px 16px
    "card_padding": "1.5rem",               # 24px
    "card_padding_lg": "2rem",              # 32px for larger cards
    "page_padding": "2.5rem",               # 40px
    "modal_padding": "2rem",                # 32px
    "input_padding": "0.75rem 1rem",        # 12px 16px
    "button_padding_sm": "0.5rem 1rem",     # 8px 16px
    "button_padding_md": "0.75rem 1.5rem",  # 12px 24px
    "button_padding_lg": "1rem 2rem",       # 16px 32px
    "stack_gap": "6",                       # 24px - between stacked items (Reflex expects '0'-'9')
    "grid_gap": "6",                        # 24px - between grid items (Reflex expects '0'-'9')
    "section_gap": "9",                     # 48px - between major sections (Reflex expects '0'-'9', 9=2.5rem=40px closest to 3rem)
}

# ============================================================================
# TYPOGRAPHY
# ============================================================================

TYPOGRAPHY = {
    # Font families
    "font_sans": "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', sans-serif",
    "font_mono": "'SF Mono', 'Monaco', 'Consolas', monospace",
}

# Typography scale (Reflex size mappings + custom properties)
HEADING_XL = {
    "size": "8",  # 36px in Reflex
    "weight": "bold",
    "line_height": "1.2",
    "letter_spacing": "-0.02em",
}

HEADING_LG = {
    "size": "7",  # 30px
    "weight": "bold",
    "line_height": "1.25",
    "letter_spacing": "-0.015em",
}

HEADING_MD = {
    "size": "6",  # 24px
    "weight": "bold",
    "line_height": "1.3",
    "letter_spacing": "-0.01em",
}

HEADING_SM = {
    "size": "5",  # 20px
    "weight": "bold",
    "line_height": "1.35",
}

BODY_LG = {
    "size": "4",  # 18px
    "weight": "regular",
    "line_height": "1.6",
}

BODY_MD = {
    "size": "3",  # 16px
    "weight": "regular",
    "line_height": "1.6",
}

BODY_SM = {
    "size": "2",  # 14px
    "weight": "regular",
    "line_height": "1.5",
}

BODY_XS = {
    "size": "1",  # 12px
    "weight": "medium",
    "line_height": "1.4",
}

LABEL = {
    "size": "1",  # 12px
    "weight": "medium",
    "text_transform": "uppercase",
    "letter_spacing": "0.05em",
}

# ============================================================================
# SHADOWS
# ============================================================================

SHADOWS = {
    "xs": "0 1px 2px rgba(0, 0, 0, 0.04)",
    "sm": "0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06)",
    "md": "0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.06)",
    "lg": "0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05)",
    "xl": "0 20px 25px rgba(0, 0, 0, 0.1), 0 10px 10px rgba(0, 0, 0, 0.04)",
    "2xl": "0 24px 48px rgba(0, 0, 0, 0.2), 0 12px 24px rgba(0, 0, 0, 0.15)",

    # Component-specific shadows
    "navbar": "0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.03)",
    "card": "0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06)",
    "card_hover": "0 4px 12px rgba(0, 0, 0, 0.1)",
    "button": "0 1px 3px rgba(37, 99, 235, 0.3), 0 1px 2px rgba(37, 99, 235, 0.2)",
    "button_hover": "0 4px 12px rgba(37, 99, 235, 0.4)",
    "modal": "0 24px 48px rgba(0, 0, 0, 0.2), 0 12px 24px rgba(0, 0, 0, 0.15)",
    "focus_ring": "0 0 0 3px rgba(37, 99, 235, 0.1)",
}

# ============================================================================
# BORDER RADIUS
# ============================================================================

RADIUS = {
    "sm": "4px",
    "md": "6px",
    "lg": "8px",
    "xl": "12px",
    "2xl": "16px",
    "full": "9999px",

    # Component-specific
    "button": "8px",
    "input": "8px",
    "card": "12px",
    "badge": "6px",
    "modal": "16px",
}

# ============================================================================
# TRANSITIONS
# ============================================================================

TRANSITIONS = {
    "fast": "all 0.15s ease",
    "base": "all 0.2s ease",
    "slow": "all 0.3s ease",
    "smooth": "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
}

# ============================================================================
# Z-INDEX LAYERS
# ============================================================================

Z_INDEX = {
    "base": "0",
    "dropdown": "10",
    "sticky": "20",
    "navbar": "50",
    "modal_overlay": "100",
    "modal": "110",
    "toast": "120",
}

# ============================================================================
# COMPONENT STYLE PRESETS
# ============================================================================

# Pre-configured style dictionaries for common components
CARD_STYLE = {
    "bg": COLORS["white"],
    "border": f"1px solid {COLORS['neutral-200']}",
    "border_radius": RADIUS["card"],
    "padding": COMPONENT_SPACING["card_padding"],
    "box_shadow": SHADOWS["card"],
    "transition": TRANSITIONS["base"],
}

CARD_HOVER_STYLE = {
    **CARD_STYLE,
    "cursor": "pointer",
    "_hover": {
        "border_color": COLORS["primary-300"],
        "box_shadow": SHADOWS["card_hover"],
        "transform": "translateY(-2px)",
    },
}

BUTTON_PRIMARY_STYLE = {
    "bg": COLORS["primary-600"],
    "color": COLORS["white"],
    "border": "none",
    "border_radius": RADIUS["button"],
    "padding": COMPONENT_SPACING["button_padding_md"],
    "font_weight": "500",
    "box_shadow": SHADOWS["button"],
    "transition": TRANSITIONS["base"],
    "cursor": "pointer",
    "_hover": {
        "bg": COLORS["primary-700"],
        "box_shadow": SHADOWS["button_hover"],
        "transform": "translateY(-1px)",
    },
    "_active": {
        "transform": "translateY(0)",
    },
}

BUTTON_SECONDARY_STYLE = {
    "bg": COLORS["white"],
    "color": COLORS["primary-600"],
    "border": f"1px solid {COLORS['primary-300']}",
    "border_radius": RADIUS["button"],
    "padding": COMPONENT_SPACING["button_padding_md"],
    "font_weight": "500",
    "transition": TRANSITIONS["base"],
    "cursor": "pointer",
    "_hover": {
        "bg": COLORS["primary-50"],
        "border_color": COLORS["primary-400"],
    },
}

BUTTON_GHOST_STYLE = {
    "bg": "transparent",
    "color": COLORS["neutral-600"],
    "border": "none",
    "border_radius": RADIUS["button"],
    "padding": COMPONENT_SPACING["button_padding_md"],
    "transition": TRANSITIONS["base"],
    "cursor": "pointer",
    "_hover": {
        "bg": COLORS["neutral-100"],
        "color": COLORS["neutral-900"],
    },
}

INPUT_STYLE = {
    "bg": COLORS["white"],
    "border": f"1px solid {COLORS['neutral-300']}",
    "border_radius": RADIUS["input"],
    "padding": COMPONENT_SPACING["input_padding"],
    "color": COLORS["neutral-900"],
    "transition": TRANSITIONS["base"],
    "_placeholder": {
        "color": COLORS["neutral-400"],
    },
    "_focus": {
        "border_color": COLORS["primary-500"],
        "box_shadow": SHADOWS["focus_ring"],
        "outline": "none",
    },
}

BADGE_SUCCESS_STYLE = {
    "bg": COLORS["success-100"],
    "color": COLORS["success-600"],
    "border": f"1px solid {COLORS['success-600']}",
    "border_radius": RADIUS["badge"],
    "padding": "0.25rem 0.5rem",
    "font_size": "0.75rem",
    "font_weight": "500",
}

BADGE_WARNING_STYLE = {
    "bg": COLORS["warning-100"],
    "color": COLORS["warning-600"],
    "border": f"1px solid {COLORS['warning-600']}",
    "border_radius": RADIUS["badge"],
    "padding": "0.25rem 0.5rem",
    "font_size": "0.75rem",
    "font_weight": "500",
}

BADGE_ERROR_STYLE = {
    "bg": COLORS["error-100"],
    "color": COLORS["error-600"],
    "border": f"1px solid {COLORS['error-600']}",
    "border_radius": RADIUS["badge"],
    "padding": "0.25rem 0.5rem",
    "font_size": "0.75rem",
    "font_weight": "500",
}

BADGE_INFO_STYLE = {
    "bg": COLORS["info-100"],
    "color": COLORS["info-600"],
    "border": f"1px solid {COLORS['info-600']}",
    "border_radius": RADIUS["badge"],
    "padding": "0.25rem 0.5rem",
    "font_size": "0.75rem",
    "font_weight": "500",
}
