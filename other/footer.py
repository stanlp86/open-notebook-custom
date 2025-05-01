import base64
from pathlib import Path
import streamlit as st

def img_to_base64(img_path):
    with open(img_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def make_footer():
    logo_path_1 = "/home/cdsw/assets/convergence.png"
    logo_base64_1 = img_to_base64(logo_path_1)
    
    # logo_path_2 = "/home/cdsw/assets/cada.png"
    # logo_base64_2 = img_to_base64(logo_path_2) #<img src="data:image/png;base64,{logo_base64_2}" alt="Logo">
    
    
    # Add some spacing to prevent content from being hidden behind the footer
    st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)
    
    # Footer with fixed positioning at the bottom
    footer = f"""
    <style>
    .footer {{
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #FFFFFF;
        color: #000000;
        text-align: center;
        padding: 10px;
        font-size: 12px;
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 999;
    }}
    .footer img {{
        margin-right: 10px;
        height: 50px;
    }}
    .footer p {{
        margin: 0;
        padding: 0;
        font-size: 14px;
    }}
    .footer a {{
        color: #4DA8DA;
        text-decoration: none;
        font-size: 14px;  /* Match the paragraph font size */
    }}
    /* Ensure the footer stays at the bottom even when content is short */
    body {{
        min-height: 100vh;
        position: relative;
    }}
    main {{
        padding-bottom: 50px;
    }}
    </style>
    <div class="footer">
        <img src="data:image/png;base64,{logo_base64_1}" alt="Logo">
        <p> <a href="mailto:brian.bierie@abbvie.com">Brian Bierie</a> • <a href="mailto:stan.pashkovski@abbvie.com">Stan Pashkovski</a> • © 2025</p>
        
    </div>
    """
    return st.markdown(footer, unsafe_allow_html=True)