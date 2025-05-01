import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from open_notebook.footer import make_footer

def convert_json_to_dataframe(json_data):
    if isinstance(json_data, dict) and "records" in json_data:
        return pd.DataFrame(json_data['records'])
    else:
        return pd.DataFrame(json_data)

def filter_dataframe(df, filters):
    filtered_df = df.copy()
    for col, min_val in filters.items():
        filtered_df = filtered_df[filtered_df[col] >= min_val]
    return filtered_df

def fetch_all_pages(base_url, initial_json_data):
    all_data = []
    max_pages = 8 if initial_json_data.get("total", 0) > 200 else float('inf')
    page = 1

    while page <= max_pages:
        url = base_url.replace("page=1", f"page={page}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            json_data = response.json()
            if not json_data.get("records"):
                break
            df = convert_json_to_dataframe(json_data)
            all_data.append(df)
            page += 1
        except requests.RequestException as e:
            st.error(f"Error fetching data from page {page}: {e}")
            break

    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

st.set_page_config(layout="wide")
st.title("Pub Tools")
make_footer()
# URL template with placeholders
url_template = ("https://asd-ws.irx.awscloud.abbvienet.com/litwatch/docs"
                "?geneSymbol={gene_symbol}&page=1&pageSize=50"
                "&sort={sort_option}&order=desc")

# User input for gene symbol, converted to uppercase
gene_symbol_input = st.text_input("Enter a gene symbol:", "TNFSF15")
gene_symbol = gene_symbol_input.upper()  # Convert to uppercase

# Dropdown for sorting option including "relevance score"
sort_option = st.selectbox("Select sorting option:", ["Journal Impact Factor", "Relevance Score", "Citations"])

# Map "relevance score" to "score" in the URL
sort_field_map = {
    "Journal Impact Factor": "journal_impact_factor",
    "Relevance Score": "score",
    "Citations": "citations"
    
}

# Create the URL based on user inputs
custom_url = url_template.format(
    gene_symbol=gene_symbol,  # Use the uppercase version
    sort_option=sort_field_map[sort_option]
)

# "Search" button
if st.button("Search"):
    try:
        response = requests.get(custom_url)
        response.raise_for_status()
        json_data = response.json()
        
        if json_data and "page=1" in custom_url:
            df = fetch_all_pages(custom_url, json_data)
        else:
            df = convert_json_to_dataframe(json_data) if json_data else pd.DataFrame()
        
        # Check if 'doi' column is present and prepend "https://doi.org" to each DOI
        if 'doi' in df.columns:
            df['doi'] = 'https://doi.org/' + df['doi'].astype(str)
        
        # Store the dataframe in session state for later use 
        st.session_state['df'] = df

    except requests.RequestException as e:
        st.error(f"Error fetching data from URL: {e}")

# Check if there's data in the session state 
if 'df' in st.session_state and not st.session_state['df'].empty:
    try:
        df = st.session_state['df']
        st.subheader("Filtered Data Preview")
        
        numeric_cols = df.select_dtypes(include='number').columns
        if 'filters' not in st.session_state:
            st.session_state.filters = {col: float(df[col].min()) for col in numeric_cols}

        if numeric_cols.empty:
            st.info("No numeric columns available for filtering.")
        else:
            with st.expander("Set Minimum Value Filters for Numeric Columns"):
                for col in numeric_cols:
                    st.session_state.filters[col] = st.number_input(
                        f"Minimum value for {col}",
                        min_value=0.0,
                        max_value=10000.0,
                        value=st.session_state.filters[col],
                        key=col
                    )

        filtered_df = filter_dataframe(df, st.session_state.filters)
        if filtered_df.empty:
            st.warning("No data is available after applying filters.")
        else:
            st.dataframe(filtered_df)

            conversion_choice = st.radio("Choose conversion format", ("CSV", "Excel"))

            if conversion_choice == "CSV":
                original_csv = df.to_csv(index=False)
                filtered_csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download Original CSV",
                    data=original_csv,
                    file_name="original_data.csv",
                    mime="text/csv"
                )
                st.download_button(
                    label="Download Filtered CSV",
                    data=filtered_csv,
                    file_name="filtered_data.csv",
                    mime="text/csv"
                )
            elif conversion_choice == "Excel":
                original_towrite = BytesIO()
                df.to_excel(original_towrite, index=False, engine='openpyxl')
                original_towrite.seek(0)

                filtered_towrite = BytesIO()
                filtered_df.to_excel(filtered_towrite, index=False, engine='openpyxl')
                filtered_towrite.seek(0)

                st.download_button(
                    label="Download Original Excel",
                    data=original_towrite,
                    file_name="original_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.download_button(
                    label="Download Filtered Excel",
                    data=filtered_towrite,
                    file_name="filtered_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Please enter a valid gene symbol and select a sorting option to fetch and display data.")

