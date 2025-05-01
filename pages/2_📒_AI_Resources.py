from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()
import streamlit as st
from humanize import naturaltime
from open_notebook.domain.notebook import Notebook
from pages.stream_app.chat import chat_sidebar
from pages.stream_app.note import add_note, note_card
from pages.stream_app.source import add_source, source_card 
from pages.stream_app.utils import setup_page, setup_stream_state
from open_notebook.footer import make_footer
from open_notebook.domain.models import model_manager # to get defaults which would typically happen in the Settings page setup we've removed. 
model_manager.refresh_defaults()


setup_page("📒 AI Assistant")
make_footer()

def notebook_header(current_notebook: Notebook):
    """
    Defines the header of the notebook page, including the ability to edit the notebook's name and description.
    """
    c1, c2, c3 = st.columns([8, 2, 2])
    c1.header(current_notebook.name)
    if c2.button("Home"):
        st.session_state["current_notebook_id"] = None
        st.rerun()

    if c3.button("Refresh"):
        st.rerun()
    current_description = current_notebook.description
    with st.expander(
        current_notebook.description
        if len(current_description) > 0
        else "click to add a description"
    ):
        notebook_name = st.text_input("Name", value=current_notebook.name)
        notebook_description = st.text_area(
            "Description",
            value=current_description,
            placeholder="Add as much context as you can as this will be used by the AI to generate insights.",
        )
        c1, c2, c3 = st.columns([1, 1, 1])
        if c1.button("Save", key="edit_notebook"):
            current_notebook.name = notebook_name
            current_notebook.description = notebook_description
            current_notebook.save()
            st.rerun()
        if not current_notebook.archived:
            if c2.button("Archive"):
                current_notebook.archived = True
                current_notebook.save()
                st.toast("Resource archived")
        else:
            if c2.button("Unarchive"):
                current_notebook.archived = False
                current_notebook.save()
                st.toast("Resource unarchived")
        if c3.button("Delete forever", type="primary"):
            current_notebook.delete()
            st.session_state["current_notebook_id"] = None
            st.rerun()


def notebook_page(current_notebook):
    # Ensure an entry for this notebook in the session state
    if current_notebook.id not in st.session_state:
        # Set "show_sources" and "show_notes" to True for automatic loading
        st.session_state[current_notebook.id] = {
            "notebook": current_notebook,
            "show_sources": False,  # Automatically show sources
            "show_notes": False     # Automatically show notes
        }

    # Setup the active session
    current_session = setup_stream_state(current_notebook=current_notebook)

    sources = current_notebook.sources
    notes = current_notebook.notes

    notebook_header(current_notebook)

    # Create a centered container
    centered_container = st.container()
    col1, col2, col3 = centered_container.columns([1, 20, 1])

    # Utilize the central column for main content
    with col2:
        sources_tab, notes_tab = st.columns([1, 1])

        with sources_tab:
            with st.container():
                # Create buttons for sources next to each other
                if st.button("Add Source", icon="➕"):
                    add_source(current_notebook.id)
                st.write("")  # Adds a small space between buttons
                if st.button("Show/Hide Sources"):
                    st.session_state[current_notebook.id]["show_sources"] = not st.session_state[current_notebook.id]["show_sources"]

                # Display each source
                if st.session_state[current_notebook.id]["show_sources"]:
                    for source in sources:
                        source_card(source=source, notebook_id=current_notebook.id)
        with notes_tab:
            with st.container():
                # Create buttons for notes next to each other
                if st.button("Write a Note", icon="📝"):
                    add_note(current_notebook.id)
                st.write("")  # Adds a small space between buttons
                if st.button("Show/Hide Notes"):
                    st.session_state[current_notebook.id]["show_notes"] = not st.session_state[current_notebook.id]["show_notes"]

                # Display each note
                if st.session_state[current_notebook.id]["show_notes"]:
                    for note in notes:
                        note_card(note=note, notebook_id=current_notebook.id)

    # Chat sidebar
    chat_sidebar(current_notebook=current_notebook, current_session=current_session)
    make_footer()
    
def notebook_list_item(notebook):
    with st.container(border=True):
        st.subheader(notebook.name)
        st.caption(
            f"Created: {naturaltime(notebook.created)}, updated: {naturaltime(notebook.updated)}"
        )
        st.write(notebook.description)
        if st.button("Open", key=f"open_notebook_{notebook.id}"):
            st.session_state["current_notebook_id"] = notebook.id
            st.rerun()


if "current_notebook_id" not in st.session_state:
    st.session_state["current_notebook_id"] = None

# todo: get the notebook, check if it exists and if it's archived
if st.session_state["current_notebook_id"]:
    current_notebook: Notebook = Notebook.get(st.session_state["current_notebook_id"])
    if not current_notebook:
        st.error("Resource not found")
        st.stop()
    notebook_page(current_notebook)
    st.stop()

st.title("Intelligence Assistant")
st.caption(
    "Tailored AI resources help to organize your thoughts, ideas, and domain specific information. You can create tailored AI resources for different research topics and projects, to create new articles, etc. "
)

with st.expander("➕ **New AI Resource**"):
    new_notebook_title = st.text_input("New Resource Name")
    new_notebook_description = st.text_area(
        "Description",
        placeholder="Explain the purpose of this AI resource. The more details the better.",
    )
    if st.button("Create a new AI Resource", icon="➕"):
        notebook = Notebook(
            name=new_notebook_title, description=new_notebook_description
        )
        notebook.save()
        st.toast("AI resource created successfully", icon="📒")

notebooks = Notebook.get_all(order_by="updated desc")
archived_notebooks = [nb for nb in notebooks if nb.archived]

for notebook in notebooks:
    if notebook.archived:
        continue
    notebook_list_item(notebook)

if len(archived_notebooks) > 0:
    with st.expander(f"**🗃️ {len(archived_notebooks)} archived AI resources**"):
        st.write("ℹ Archived AI resources can still be accessed and used in search.")
        for notebook in archived_notebooks:
            notebook_list_item(notebook)

