"""
Created on Tue Sep 17 13:11:34 2024

@author: BIERIBR
"""

import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import io
import os
import re

from open_notebook.footer import make_footer

ILIAD_URL = os.environ.get("ILIAD_URL")
ILIAD_KEY = os.environ.get("ILIAD_KEY")

st.set_page_config(layout="wide")


system_prompt = """
For each row in the table, containing evidence of therapeutic potential of a gene in the treatment of a disease, perform the following queries. All responses should be formatted in the same way as a single paragraph (excluding the title).  Also, none of the words in any response should be flanked by << and >>. Strength numbers should always be represented as an integer in the responses. Do not use the terms "row", "row number", "query", or "query number" in the response."""

questions = [
    "Query 1: <<Clinical Evidence>> If the value for the column [Number of Drugs Phase 3+] is greater than 0, then report that there is strong clinical evidence to support the therapeutical potential of the Gene and the Disease as at least one drug that targets this mechanism is Phase 3 or beyond. If the values for the column [Number of Drugs Phase 1-2] is greater than 0 or the value for the column [Number of Drugs Preclinical] is greater than zero, then report that additional drugs that target this mechanism are in earlier stages of clinical development. Else if the value for the column [Number of Drugs Phase 1-2] is greater than 0, then report that there is emerging clinical evidence to support the therapeutical potential of the Gene and the Disease as at least one drug that targets this mechanism is in early clinical development (Phase 1 or 2). If the values for the column [Number of Drugs Preclinical] is greater than zero, then report that additional drugs that target this mechanism are in preclinical development. Else if the value for the column [Number of Drugs Preclinical] is greater than 0, then report that there is preclinical evidence to support the therapeutical potential of the Gene and the Disease as at least one drug that targets this mechanism is in preclinical development. Else report that there are no drugs that target this mechanism that have been reported to be in preclinical or clinical development. Only return the Report and Additional Report as a single sentence in the response.",
    "Query 2: <<Human Genetic Evidence>> From the table, perform the following queries. If the value for the column [Human Genetics Strength] is equal to 3, then report that, based on expert curation of genetic evidence compiled by the GRC, there is strong genetic evidence (Strength = 3) to support an association between the gene and disease. Else if the value for the column [Human Genetics Strength] is equal to 2, then report that, based on expert curation of genetic evidence compiled by the GRC, there is moderate genetic evidence (Strength = 2) to support an association between the gene and disease.  Else if the value for the column [Human Genetics Strength] is equal to 1, then report that, based on expert curation of genetic evidence compiled by the GRC, there is weak genetic evidence (Strength = 1) to support an association between the gene and disease.  Else if the value for the column [Human Genetics Strength] is not empty, then report that, based on expert curation of genetic evidence compiled by the GRC, there is no genetic evidence (Strength = 0) to support an association between the gene and disease.  Else if the column [Human Genetics Strength] is empty, then report that, a Human Genetics Strength score was not generated for this disease and combination.",
    "Query 3: <<Graph Evidence>> From the table, perform the following queries. If the value for the column [Graph Ranking Strength] is equal to 3, then report that, based on an analysis of all lines of evidence in the AbbVie Knowledge Graph, there is a very strong association (z-score > 4, Strength = 3) between the gene and disease. Else if the value for the column [Graph Ranking Strength] is equal to 2, then report that, based on an analysis of all lines of evidence in the AbbVie Knowledge Graph, there is a strong association (z-score > 3, Strength = 2) between the gene and disease. Else if the value for the column [Graph Ranking Strength] is equal to 1, then report that, based on an analysis of all lines of evidence in the AbbVie Knowledge Graph, there is a moderate association (z-score > 2, Strength = 1) between the gene and disease. Else report that, based on an analysis of all lines of evidence in the AbbVie Knowledge Graph, there is no statistically differentiated association (z-score < 2, Strength = 0) between the gene and disease.",
    "Query 4: <<Disease Priority Index Evidence>> From the table below, perform the following queries. If the value for the column [Target Probability Strength] is equal to 3, then report that, based on a customized multi-omic analysis by the GRC on curated data, there is a very strong association (gene ranked in the top 0.5% of all genes, Strength = 3) between the gene and disease. Else if the value for the column [Target Probability Strength] is equal to 2, then report that, based on a customized multi-omic analysis by the GRC on curated data, there is a strong association (gene ranked in the top 0.5-1.0% of all genes, Strength = 2) between the gene and disease. Else if the value for the column [Target Probability Strength] is equal to 1, then report that, based on a customized multi-omic analysis by the GRC on curated data, there is a moderate association (gene ranked in the top 1-2% of all genes, Strength = 1) between the gene and disease. Else if the value for the column [Target Probability Strength] is not empty, then report that, based on a customized multi-omic analysis by the GRC on curated data, there is no statistically differentiated association (not ranked in the top 2% of genes, Strength = 0) between the gene and disease. Else if the column [Target Probability Strength] is empty, then report that, a Disease Priority Index score was not generated for this disease and gene combination.",
    "Query 5: <<Literature Momentum>> From the table below, perform the following queries. If the value for the column [Literature Momentum Strength] is equal to 3, then report that, based on a statistical analysis of co-mentions in the scientific literature, there is a significant increase (Strength = 3) in the mentions of the Gene and Health Condition in the most recent year of the analysis compared to previous years. This suggests a strong and growing scientific interest in this target-disease pair. Else if the value for the column [Literature Momentum Strength] is equal to 2, then report that, based on a statistical analysis of co-mentions in the scientific literature, there is a moderate increase (Strength = 2) in the mentions of the Gene and Health Condition in the most recent year of the analysis compared to previous years. This suggests a growing scientific interest in this target-disease pair. Else if the value for the column [Literature Momentum Strength] is equal to 1, then report that, based on a statistical analysis of co-mentions in the scientific literature, there is a slight but measurable increase (Strength = 1) in the mentions of the Gene and Health Condition in the most recent year of the analysis compared to previous years. This may suggest an emerging scientific interest in this target-disease pair. Else report that, based on a statistical analysis of co-mentions in the scientific literature, there is no meaningful change (Strength = 0) in the mentions of the Gene and Health Condition in the most recent year of the analysis compared to previous years. This does not suggest a lack of scientific interest in this target-disease pair, but simply that there is no recent increase in the number of citations.",
    "Query 6: <<Literature Evidence>> From the table below, perform the following queries. List in sentence format the number of literature references from Tellic (column [Literature Support]) and IPA (column [IPA Number of Findings]). Also list the number of variants mediating the gene and disease according to Tellic (column [Number of Mediating Variants (tellic)]).",
    "Query Summary: <<Query Summary>> Provide a summary of all query responses formatted as a single paragraph following the individual query results for each row. Do not add information or interpretations that are not included in the query responses. Also, exclude the Biotarget Linkage Strength information from the summary."
]

def get_token():
    token_url = os.getenv("TOKEN_URL")
    username = os.getenv("LOGIN")
    password = os.getenv("PSSWD")

    try:
        response = requests.get(token_url, auth=HTTPBasicAuth(username, password), verify=False)
        if response.status_code == 200:
            token_json = response.json()
            auth_token = token_json.get("token")
            
            if auth_token:
                st.write("ARCH access granted")
                return auth_token
            else:
                st.error("Authentication error")
                return None
        else:
            st.error(f"Failed to retrieve credentials. HTTP Status: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

def get_gpt4o_response(question, context):
    full_prompt = context + question

    url = f"{ILIAD_URL}/api/v1/chat/gpt-4o"
    response = requests.post(
        url=url,
        json={
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt}
            ],
            "Temperature": 0.0,
            "max_tokens": 4096
        },
        headers={"x-api-key": ILIAD_KEY}
    )
    response.raise_for_status()
    return response.json()

def generate_summary_table(response_df):
    df_as_text = response_df.to_string()
    summary_prompt = f"Based on the following responses:\n{df_as_text}\n\nProvide a summarized table based on the data. Do not add columns that are not present in {df_as_text}, and exclude the summary column from {df_as_text} when generating the new table. The summary should include only the qualitative descriptors and strength scores or numbers of items. Make sure the format is consistent between the cells in each column. In the Literature Support column, the format should resemble the following example: 2,283 literature references, 46 IPA findings, 11 mediating variants."
    response = get_gpt4o_response("Create a summary table from data.", summary_prompt)
    return response["completion"]["content"]

def process_responses(data):
    st.subheader("Disease-Gene Evidence Overview")

    responses_list = []
    for index, row in data.iterrows():
        row_content = row.to_string()
        first_column_value = row.iloc[0]
        context = f"Row {index + 1}:\n{row_content}\n\n"

        st.markdown(f"<h4 style='color: green;'>DGEM analyses for {first_column_value}:</h4>", unsafe_allow_html=True)
        
        row_responses = {"Gene": first_column_value}

        for question in questions:
            try:
                question_title = re.findall(r'<<(.+?)>>', question)[0]
                required_columns = list(set(re.findall(r'\[(.*?)\]', question)))
                missing_columns = [col for col in required_columns if col not in data.columns]

                if not missing_columns:
                    data_response = get_gpt4o_response(question, context)
                    response_content = data_response["completion"]["content"]
                    st.write(f"**{first_column_value}: {question_title}**")
                    st.write(response_content)
                    row_responses[question_title] = response_content

            except Exception as e:
                st.error(f"An error occurred: {e}")

        responses_list.append(row_responses)

    response_df = pd.DataFrame(responses_list).set_index("Gene")
    summary_table = generate_summary_table(response_df)

    st.write("**Summary Table**")
    st.markdown(summary_table)

def hide_streamlit_default_ui():
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        footer:after {
            content: 'DGEM Assistant    >    Using uploaded file for dynamic responses';
            visibility: visible;
            display: block;
            position: relative;
            padding: 10px;
            top: 2px;
            color: #666;
            text-align: left;
        }
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def process_uploaded_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            data = pd.read_csv(uploaded_file)
        else:
            data = pd.read_excel(uploaded_file, engine='openpyxl')
        run_analysis(data)
    except Exception as e:
        st.error(f"An error occurred: {e}")

def process_downloaded_file(url, auth_token):
    if st.session_state.get('download_source') and st.session_state.get('downloaded_option_url') == url:
        data = st.session_state['original_data']  # Use the previously downloaded data

    else:
        try:
            headers = {'Authorization': f'Bearer {auth_token}'}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = pd.read_csv(io.StringIO(response.text))
            st.session_state['original_data'] = data
            st.session_state['downloaded_option_url'] = url  # Save the URL to track the download source
            st.session_state['download_source'] = True

        except Exception as e:
            st.error(f"An error occurred fetching the file: {e}")
    run_analysis(data)

# Function to perform analysis on the given data
def run_analysis(data):
    data = data.dropna(axis=1, how='all')  # Drop columns with all NaN values

    # Convert columns with float values to int, where applicable
    for column in data.columns:
        if pd.api.types.is_float_dtype(data[column]):
            data[column] = data[column].apply(lambda x: int(x) if pd.notnull(x) else x)

    # Initialize Streamlit session state variables
    session_vars = ['gene_list', 'gene_list_input', 'selected_values', 'min_values', 'sort_by_col', 'num_rows',
                    'include_only_zero_phase3']
    for var in session_vars:
        if var not in st.session_state:
            if var in ['gene_list', 'selected_values', 'min_values']:
                st.session_state[var] = {}
            elif var == 'include_only_zero_phase3':
                st.session_state[var] = False
            elif var == 'num_rows':
                st.session_state[var] = 5
            else:
                st.session_state[var] = ''

    # UI for clearing filter states
    def clear_filter_states():
        st.session_state['selected_values'] = {}
        st.session_state['min_values'] = {}

    # Process gene symbols input
    def process_gene_symbols():
        clear_filter_states()
        if st.session_state['gene_list_input']:
            gene_list = re.split(r'[,\n]+', st.session_state['gene_list_input'].strip())
            st.session_state['gene_list'] = [gene.strip() for gene in gene_list if gene.strip()]

    # Clear gene symbols input
    def clear_gene_symbols():
        st.session_state['gene_list'] = []
        st.session_state['gene_list_input'] = ''
        clear_filter_states()

    # Start with a placeholder for filtered data
    filtered_data = data.copy()

    # User interface for data filtering options
    st.markdown("<hr style='border: 0.5px solid; margin: 1px 0;'>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:green;font-weight:bold;'>Data Filtering Options</h4>", unsafe_allow_html=True)

    # Checkbox to include only rows with 0 in 'Number of Drugs Phase 3+' column
    include_only_zero_phase3 = st.checkbox(
        'Include only rows with 0 in "Number of Drugs Phase 3+" column',
        value=st.session_state['include_only_zero_phase3']
    )

    # Execute filtering based on the checkbox state
    if include_only_zero_phase3:
        if 'Number of Drugs Phase 3+' in filtered_data.columns:
            try:
                filtered_data = filtered_data[filtered_data['Number of Drugs Phase 3+'] == 0]
            except Exception as e:
                st.error(f"An error occurred while filtering: {e}")

    # Text area for gene symbol input
    st.session_state['gene_list_input'] = st.text_area(
        "Paste a list of Gene symbols to filter (comma or newline separated):",
        value=st.session_state['gene_list_input'],
        height=100
    )

    # Submit, clear, and reset buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("Submit Gene Symbols", on_click=process_gene_symbols)
    with col2:
        st.button("Clear Gene Symbols", on_click=clear_gene_symbols)
    with col3:
        st.button("Clear Numerical Filters", on_click=clear_filter_states)

    if st.session_state['gene_list']:
        filtered_data = filtered_data[filtered_data['Gene'].isin(st.session_state['gene_list'])]

    # Validate and adjust numerical filters
    def validate_and_adjust_filters(data):
        temp_filtered_data = data.copy()
        for column in data.columns:
            if column in st.session_state['selected_values']:
                selected_vals = st.session_state['selected_values'][column]
                temp_filtered_data = temp_filtered_data[temp_filtered_data[column].isin(selected_vals)]

        for column in temp_filtered_data.columns:
            if pd.api.types.is_numeric_dtype(temp_filtered_data[column]):
                valid_values = temp_filtered_data[column].dropna().unique().astype(int).tolist()

                if column in st.session_state['selected_values']:
                    currently_selected = st.session_state['selected_values'][column]
                    st.session_state['selected_values'][column] = [v for v in currently_selected if v in valid_values]

                if column in st.session_state['min_values']:
                    min_val = temp_filtered_data[column].min()
                    if st.session_state['min_values'][column] < min_val:
                        st.session_state['min_values'][column] = int(min_val)

    validate_and_adjust_filters(filtered_data)

    # UI for handling column-specific filters
    fcol1, fcol2 = st.columns(2)
    columns = filtered_data.columns.tolist()
    mid_index = (len(columns) + 1) // 2

    def handle_filter_column(column, filtered_data):
        numeric_column = filtered_data[column].dropna()
        if numeric_column.empty:
            st.warning(f"Column '{column}' has no numeric data to filter.")
            return filtered_data

        unique_values = numeric_column.unique().astype(int)

        if "strength" in column.lower():
            selected_values = st.multiselect(
                f"Filter values for {column} (leave empty for all):",
                options=list(unique_values),
                default=st.session_state['selected_values'].get(column, [])
            )
            st.session_state['selected_values'][column] = selected_values
            if selected_values:
                return filtered_data[filtered_data[column].isin(selected_values)]
        else:
            min_val, max_val = int(numeric_column.min()), int(numeric_column.max())
            min_value = st.number_input(
                f"Set minimum {column} ({min_val}-{max_val}):",
                value=st.session_state['min_values'].get(column, min_val),
                step=1
            )
            st.session_state['min_values'][column] = min_value
            return filtered_data[filtered_data[column] >= min_value]

        return filtered_data

    with fcol1:
        for column in columns[:mid_index]:
            if pd.api.types.is_numeric_dtype(filtered_data[column]):
                filtered_data = handle_filter_column(column, filtered_data)
            elif column != "Gene":
                st.write(f"Column '{column}' is non-numeric and will not be filtered.")

    with fcol2:
        for column in columns[mid_index:]:
            if pd.api.types.is_numeric_dtype(filtered_data[column]):
                filtered_data = handle_filter_column(column, filtered_data)
            elif column != "Gene":
                st.write(f"Column '{column}' is non-numeric and will not be filtered.")

    num_filtered_rows = len(filtered_data.dropna(how='all'))
    st.markdown(
        f"<span style='color:green; font-weight:bold;'>Number of rows after filtering: {num_filtered_rows}</span>",
        unsafe_allow_html=True
    )

    # Additional options and sorting section
    st.markdown("<hr style='border: 0.5px solid; margin: 1px 0;'>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:green;font-weight:bold;'>Additional Options</h4>", unsafe_allow_html=True)

    if columns:
        sort_options = [col for col in columns if col != 'Gene']

        if sort_options:
            default_sort_col = st.session_state.get('sort_by_col', sort_options[0])
            if default_sort_col not in sort_options:
                default_sort_col = sort_options[0]

            st.session_state['sort_by_col'] = st.selectbox(
                "Select feature to use for sorting (descending order):",
                sort_options,
                index=sort_options.index(default_sort_col)
            )

            sorted_data = filtered_data.sort_values(by=st.session_state['sort_by_col'], ascending=False)
        else:
            st.warning("No sortable columns available.")
            sorted_data = filtered_data
    else:
        st.warning("No columns available for sorting.")
        sorted_data = filtered_data

    st.session_state['num_rows'] = st.slider(
        "Select maximum number of genes to include in the analysis:",
        1, min(len(sorted_data), 15), st.session_state.get('num_rows', 5)
    )

    trimmed_data = sorted_data.head(st.session_state['num_rows'])

    styled_data_html = (
        trimmed_data.reset_index(drop=True)
        .style
        .format(na_rep="", precision=0)
        .set_table_styles([{'selector': 'td', 'props': [('text-align', 'center')]}])
        .to_html()
    )
    st.markdown(styled_data_html, unsafe_allow_html=True)

    # Store the original data in session state if not already done
    if 'original_dataset' not in st.session_state:
        st.session_state['original_dataset'] = data.copy()

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    output_placeholder = st.empty()

    button_style = """
        <style>
        .centered-button {
            display: flex;
            justify-content: center;
        }
        </style>
    """

    st.markdown(button_style, unsafe_allow_html=True)

    with col1:
        st.markdown('<div class="centered-button">', unsafe_allow_html=True)
        send_to_ai = st.button("**Send to AI Assistant**")
        st.markdown('</div>', unsafe_allow_html=True)

    # Prepare DataFrames for download
    final_csv = trimmed_data.to_csv(index=False).encode('utf-8')
    full_filtered_csv = filtered_data.to_csv(index=False).encode('utf-8')
    original_csv = data.to_csv(index=False).encode('utf-8')

    with col2:
        st.markdown('<div class="centered-button">', unsafe_allow_html=True)
        st.download_button(
            label="Final Table as CSV",
            data=final_csv,
            file_name='final_table.csv',
            mime='text/csv',
            key='download_trimmed'
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="centered-button">', unsafe_allow_html=True)
        st.download_button(
            label="Full Filtered Dataset as CSV",
            data=full_filtered_csv,
            file_name='full_filtered_dataset.csv',
            mime='text/csv',
            key='download_filtered'
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="centered-button">', unsafe_allow_html=True)
        st.download_button(
            label="Original Dataset as CSV",
            data=original_csv,
            file_name='original_dataset.csv',
            mime='text/csv',
            key='download_original'
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # Output for send to AI button
    if send_to_ai:
        with output_placeholder.container():
            process_responses(trimmed_data)            
            
# Function to read options from a CSV file
def load_options_from_csv(filepath):
    try:
        options_data = pd.read_csv(filepath)
        return options_data
    except FileNotFoundError:
        st.error("Options CSV file not found.")
        return None
    except pd.errors.EmptyDataError:
        st.error("Options CSV is empty.")
        return None
    except Exception as e:
        st.error(f"An error occurred reading the options CSV: {e}")
        return None

# Function to display dropdown and file upload options
def display_dropdown_and_file_upload(options_data, auth_token):
    if options_data is not None:
        if 'name' in options_data.columns and 'url' in options_data.columns:
            options = options_data['name'].tolist()

            # Insert a placeholder option and CSV upload option at the beginning
            options.insert(0, "Select an indication")
            options.append("Upload an alternate UTF-8 CSV or xlsx DGEM file")

            # Set index to start with the placeholder
            selected_option = st.selectbox("**Therapeutic area datasets:**", options, index=0)

            # Handle the selected option logic
            if selected_option == "Upload an alternate UTF-8 CSV or xlsx DGEM file":
                uploaded_file = st.file_uploader("Upload file here", type=["csv", "xlsx"])
                if uploaded_file is not None:
                    process_uploaded_file(uploaded_file)

            elif selected_option != "Select an indication" and auth_token:
                file_url = options_data.loc[options_data['name'] == selected_option, 'url'].values[0]
                process_downloaded_file(file_url, auth_token)
        else:
            st.error("Columns 'name' and 'url' must be present in the options CSV.")

# Function for processing uploaded files
def process_uploaded_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            data = pd.read_csv(uploaded_file)
        else:
            data = pd.read_excel(uploaded_file, engine='openpyxl')
        run_analysis(data)
    except Exception as e:
        st.error(f"An error occurred processing the file: {e}")

# Function for processing files downloaded via URL
def process_downloaded_file(url, auth_token):
    try:
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = pd.read_csv(io.StringIO(response.text))
        run_analysis(data)
    except Exception as e:
        st.error(f"An error occurred fetching the file: {e}")


# Main function to run the Streamlit app
def main():
    hide_streamlit_default_ui()
    st.markdown("<h1 style='color:green;'>DGEM Assistant</h1>", unsafe_allow_html=True)
    make_footer()
    auth_token = get_token()

    options_csv_path = '/home/cdsw/pages/ref_files/dgem_options.csv'
    options_data = load_options_from_csv(options_csv_path)
    if options_data is not None:
        display_dropdown_and_file_upload(options_data, auth_token)

# Entry point when running the script
if __name__ == "__main__":
    main()