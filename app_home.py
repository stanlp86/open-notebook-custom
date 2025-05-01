import streamlit as st
from dotenv import load_dotenv

load_dotenv()
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import NotFoundError
from pages.components import (
    note_panel,
    source_embedding_panel,
    source_insight_panel,
    source_panel,
)
from pages.stream_app.utils import setup_page
import requests, os
from requests.auth import HTTPBasicAuth
import json
import pandas as pd


token_url = "https://gprd-auth.abbvienet.com:8110/auth.service/auth/token"
response = requests.get(
    token_url,
    auth=HTTPBasicAuth(os.getenv("USERNAME"), os.getenv("ABV_PWD")),
    verify=False,
)
auth_token = ""
if response.status_code == 200:
    token_json = response.json()
    auth_token = token_json.get("token")
    os.environ["AUTH_TOKEN"] = auth_token

setup_page("AI Assistant", sidebar_state="collapsed")

if "object_id" not in st.query_params:
    st.switch_page("pages/2_📒_AI_Resources.py")
    st.stop()

object_id = st.query_params["object_id"]
try:
    obj = ObjectModel.get(object_id)
except NotFoundError:
    st.switch_page("pages/2_📒_AI_Resources.py")
    st.stop()

obj_type = object_id.split(":")[0]

if obj_type == "note":
    note_panel(object_id)
elif obj_type == "source":
    source_panel(object_id)
elif obj_type == "source_insight":
    source_insight_panel(object_id)
elif obj_type == "source_embedding":
    source_embedding_panel(object_id)
    
