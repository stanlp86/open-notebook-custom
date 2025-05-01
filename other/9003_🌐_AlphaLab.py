# -*- coding: utf-8 -*-
"""
Created on Tue Sep 17 13:11:34 2024

@author: BIERIBR
"""
import requests
import os
import time
import sys
import traceback
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from open_notebook.domain.notebook import Notebook, Note
from open_notebook.footer import make_footer

from loguru import logger
logger.info("Starting PubLab integration with Open Notebook")

try:
    load_dotenv()
    logger.info("Environment variables loaded")
except Exception as e:
    logger.error(f"Failed to load environment variables: {e}")
    st.error(f"Failed to load environment variables: {e}")

# Load environment variables with fallbacks
ILIAD_URL = os.getenv("ILIAD_URL")
ILIAD_KEY = os.getenv("ILIAD_KEY")
logger.debug(f"ILIAD_URL configured: {bool(ILIAD_URL)}")
logger.debug(f"ILIAD_KEY configured: {bool(ILIAD_KEY)}")

# Streamlit app
st.title("Statement crosscheck via PubLab")
make_footer()
# Keep track of responses in session state
if "publab_responses" not in st.session_state:
    st.session_state.publab_responses = {
        "claude": None,
        "o3": None,
        "query": None,
        "context": None
    }

# Define user inputs
variable1 = st.text_input("Context: gene, drug, drug class:")
variable2 = st.text_input("Context: disease, indication, condition:")
variable4 = st.text_area("Statements for validation:")

# Convert variable4 to a string
variable4_str = str(variable4)

# Define the query with variables
query = f"Carefully analyze the following to determine if every claim related to {variable1} and {variable2} is supported by the literature or not.\n{variable4_str}."
query_complete = str(query)
query2 = f"Carefully analyze the following to determine if every claim related to {variable1} and {variable2} is supported by the literature or not.\n{variable4_str}."
query_complete2 = str(query2)

def ask_model_A(query):
    """
    Function to send a query to model A and retrieve the response.
    """
    logger.info("Sending request to Claude 3.7 Sonnet")
    logger.debug(f"Query to Claude: {query[:100]}...")  # Log first 100 chars of query
    try:
        if not ILIAD_URL or not ILIAD_KEY:
            logger.error("ILIAD_URL or ILIAD_KEY not configured properly")
            st.error("API configuration missing. Please check your .env file.")
            return None

        logger.debug(f"Making POST request to {ILIAD_URL}/api/v1/ask/publab")
        resp = requests.post(
            url=f"{ILIAD_URL}/api/v1/ask/publab",
            headers={"x-api-key": "iPjKT40jzw8z9YqfF40LPFoNBRDetsRG"},
            json={"messages": [{"role": "user", "content": query_complete}], "model": "claude-3.7-sonnet"}
        )
        logger.debug(f"Response status code: {resp.status_code}")
        resp.raise_for_status()
        response_json = resp.json()
        logger.info("Successfully received response from Claude 3.7 Sonnet")
        logger.debug(f"Response keys: {response_json.keys()}")
        return response_json
    except requests.RequestException as e:
        logger.error(f"Request to Claude 3.7 Sonnet failed: {e}")
        logger.error(traceback.format_exc())
        st.error(f"Request to Claude 3.7 Sonnet failed: {e}")
        return None

def ask_model_B(query_complete):
    """
    Function to send a query to model B and retrieve the response.
    """
    logger.info("Sending request to gpt-4o")
    logger.debug(f"Query to gpt-4o: {query_complete[:100]}...")  # Log first 100 chars of query
    try:
        if not ILIAD_URL or not ILIAD_KEY:
            logger.error("ILIAD_URL or ILIAD_KEY not configured properly")
            st.error("API configuration missing. Please check your .env file.")
            return None

        logger.debug(f"Making POST request to {ILIAD_URL}/api/v1/ask/publab")
        resp = requests.post(
            url=f"{ILIAD_URL}/api/v1/ask/publab",
            headers={"x-api-key": "iPjKT40jzw8z9YqfF40LPFoNBRDetsRG"},
            json={"messages": [{"role": "user", "content": query_complete2}], "model": "gpt-4o"}
        )
        logger.debug(f"Response status code: {resp.status_code}")
        resp.raise_for_status()
        response_json = resp.json()
        logger.info("Successfully received response from gpt-4o")
        logger.debug(f"Response keys: {response_json.keys()}")
        return response_json
    except requests.RequestException as e:
        logger.error(f"Request to gpt-4o failed: {e}")
        logger.error(traceback.format_exc())
        st.error(f"Request to gpt-4o failed: {e}")
        return None

if st.button("Submit"):
    logger.info("Submit button clicked")
    if query_complete:
        logger.info("Processing query")
        st.write(f"\n### PubLab cross-referencing in-progress: \n")

        # First Model: Claude 3.7 Sonnet
        st.write(f"Statements provided for the crosscheck via PubLab:\n")
        st.write(f"{query_complete}\n")
        st.write(f"#### Claude 3.7 Sonnet PubLab response: ")

        # Show spinner while waiting for Claude response
        with st.spinner('Waiting for Claude 3.7 Sonnet response...'):
            logger.info("Calling Claude 3.7 Sonnet model")
            response_model_A = ask_model_A(query_complete)

        if response_model_A:
            logger.info("Received response from Claude 3.7 Sonnet")
            answer_claude = response_model_A.get("answer", "No answer returned")
            logger.debug(f"Claude response length: {len(answer_claude)} characters")
            # Store in session state
            st.session_state.publab_responses["claude"] = answer_claude
            st.session_state.publab_responses["query"] = query_complete
            st.session_state.publab_responses["context"] = f"{variable1} and {variable2}"
            st.write("\n")
            st.write(answer_claude)
            st.write("\n")
            st.markdown(f"View referenced publications in PubLab")
            st.write("\n")
            st.write("Cost: ", response_model_A.get("cost", "Unknown"))
            st.write("\n")
            time.sleep(3)

        # Second Model: gpt-4o
        st.write(f"#### gpt-4o PubLab response:")

        # Show spinner while waiting for gpt-4o response
        with st.spinner('Waiting for gpt-4o response...'):
            logger.info("Calling gpt-4o model")
            response_model_B = ask_model_B(query_complete2)

        if response_model_B:
            logger.info("Received response from gpt-4o")
            answer_gpt_4o = response_model_B.get("answer", "No answer returned")
            logger.debug(f"gpt-4o response length: {len(answer_gpt_4o)} characters")
            # Store in session state
            st.session_state.publab_responses["o3"] = answer_gpt_4o
            st.write("\n")
            st.write(answer_gpt_4o)
            st.write("\n")
            st.markdown(f"View referenced publications in PubLab")
            st.write("\n")
            st.write("Cost: ", response_model_B.get("cost", "Unknown"))
            st.write("\n\n")
            time.sleep(5)
    else:
        logger.warning("Empty query submitted")
        st.warning("Please enter a query")

# Show note saving form only if we have responses
if st.session_state.publab_responses["claude"] or st.session_state.publab_responses["o3"]:
    st.subheader("Save Response as Note")
    with st.form("save_note_form"):
        try:
            notebooks = Notebook.get_all(order_by="name asc")
            logger.debug(f"Loaded {len(notebooks)} notebooks for the form")
            notebook = st.selectbox(
                "Select Notebook",
                notebooks,
                format_func=lambda x: x.name
            )
            response_type = st.radio(
                "Select Response to Save",
                ["Claude 3.7 Sonnet", "gpt-4o", "Both Responses"]
            )
            note_title = st.text_input(
                "Note Title (optional)",
                value=f"PubLab Check: {st.session_state.publab_responses['context']}"
            )
            submit_button = st.form_submit_button("Save as Note")

            if submit_button:
                logger.info(f"Form submitted to save {response_type} as note")
                try:
                    # Build content based on selection
                    if response_type == "Claude 3.7 Sonnet":
                        content = f"Context: {st.session_state.publab_responses['context']}\n\n"
                        content += f"Query: {st.session_state.publab_responses['query']}\n\n"
                        content += f"Claude 3.7 Sonnet Response:\n{st.session_state.publab_responses['claude']}"
                    elif response_type == "gpt-4o":
                        content = f"Context: {st.session_state.publab_responses['context']}\n\n"
                        content += f"Query: {st.session_state.publab_responses['query']}\n\n"
                        content += f"gpt-4o Response:\n{st.session_state.publab_responses['o3']}"
                    else:
                        content = f"Context: {st.session_state.publab_responses['context']}\n\n"
                        content += f"Query: {st.session_state.publab_responses['query']}\n\n"
                        content += f"Claude 3.7 Sonnet Response:\n{st.session_state.publab_responses['claude']}\n\n"
                        content += f"gpt-4o Response:\n{st.session_state.publab_responses['o3']}"

                    # Create and save the note
                    logger.debug(f"Creating note with title: {note_title}")
                    logger.debug(f"Content length: {len(content)} characters")
                    logger.debug(f"Selected notebook ID: {notebook.id}")
                    note = Note(
                        title=note_title,
                        content=content,
                        note_type="ai"
                    )
                    note.save()
                    logger.info(f"Note created with ID: {note.id}")
                    note.add_to_notebook(notebook.id)
                    logger.info(f"Note added to notebook {notebook.name} (ID: {notebook.id})")
                    st.success("Note saved successfully!")
                except Exception as e:
                    logger.error(f"Error saving note: {str(e)}")
                    logger.error(traceback.format_exc())
                    st.error(f"Failed to save note: {str(e)}")
        except Exception as e:
            logger.error(f"Error setting up note form: {str(e)}")
            logger.error(traceback.format_exc())
            st.error(f"Error setting up note form: {str(e)}")

