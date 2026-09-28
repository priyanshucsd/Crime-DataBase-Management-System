import pandas as pd
import streamlit as st
from datetime import date, datetime
import database as db
from database import DatabaseError


# PAGE SETUP

st.set_page_config(
    page_title="Crime Database Management System",
    page_icon="🚔",
    layout="wide",
)


# HELPER FUNCTIONS  (reused by every page)
def flash(message, kind="success"):
    """
    Save a message that survives st.rerun().
    Used after add / update / delete so the user still sees the result.
    """
    st.session_state["flash"] = (kind, message)


def show_flash():
    """Show and clear the saved message (if any)."""
    if "flash" in st.session_state:
        kind, message = st.session_state.pop("flash")
        if kind == "success":
            st.success(message)
        elif kind == "warning":
            st.warning(message)
        else:
            st.error(message)


def safe_fetch(func, *args):
    """Call a fetch function from database.py; on error show it and return []."""
    try:
        return func(*args)
    except DatabaseError as e:
        st.error(str(e))
        return []


def show_table(rows, empty_message="No records found."):
    """Display a list of dictionaries as a table."""
    if not rows:
        st.info(empty_message)
        return
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(f"{len(rows)} record(s)")


def option_map(options):
    """
    Turn [{'id': 1, 'label': '1 - Rahul'}, ...] into {'1 - Rahul': 1, ...}
    so it can be used with st.selectbox.
    """
    return {opt["label"]: opt["id"] for opt in options}

def index_of(options, value):
    """Position of value in a list (0 if missing). Used to pre-select dropdowns."""
    return options.index(value) if value in options else 0


def valid_phone(phone):
    """Empty is allowed; otherwise digits only, 7 to 15 characters."""
    phone = phone.strip()
    return phone == "" or (phone.isdigit() and 7 <= len(phone) <= 15)


PHONE_ERROR = "Phone must contain only digits (7 to 15 digits)."


def pick_record(rows, id_field, label_func, key, label="Select record"):
    """
    Show a dropdown of records and return the chosen record (a dictionary).
    rows       : list of dictionaries from database.py
    id_field   : name of the primary key column
    label_func : function that builds the text shown in the dropdown
    """
    lookup = {r[id_field]: r for r in rows}
    chosen_id = st.selectbox(label, list(lookup.keys()),
                             format_func=lambda i: label_func(lookup[i]), key=key)
    return lookup[chosen_id]

NO_CRIMINAL = "— Unknown / not identified —"


def index_of_value(mapping, value):
    """
    mapping is {label: id}. Returns the position of the label whose id == value,
    so a dropdown can be pre-selected when updating a record.
    """
    for position, stored_value in enumerate(mapping.values()):
        if stored_value == value:
            return position
    return 0


def next_case_number():
    """Suggest the next FIR number, e.g. FIR-2026-009."""
    cases = safe_fetch(db.get_all_cases)
    next_id = max([c["case_id"] for c in cases], default=0) + 1
    return f"FIR-{date.today().year}-{next_id:03d}"

def coming_soon(title):
    st.header(title)
    st.info("This page will be added in the next step.")


# CONNECTION CHECK 
try:
    db.test_connection()
except DatabaseError as e:
    st.title("🚔 Crime Database Management System")
    st.error(str(e))
    st.info("Fix the settings in the DB_CONFIG section of database.py "
            "and refresh this page.")
    st.stop()


# DASHBOARD PAGE
def dashboard_page():
    st.header("📊 Dashboard")
    show_flash()

    try:
        stats = db.get_dashboard_stats()
    except DatabaseError as e:
        st.error(str(e))
        return

    row1 = st.columns(4)
    row1[0].metric("Total Criminals", stats["total_criminals"])
    row1[1].metric("Total Victims", stats["total_victims"])
    row1[2].metric("Total Police Officers", stats["total_officers"])
    row1[3].metric("Total Crimes", stats["total_crimes"])

    row2 = st.columns(4)
    row2[0].metric("Total Cases", stats["total_cases"])
    row2[1].metric("Open Cases", stats["open_cases"],
                   help="Status: Open or Under Investigation")
    row2[2].metric("Closed Cases", stats["closed_cases"],
                   help="Status: Solved or Closed")

    st.divider()
    st.subheader("Recent Crimes")
    recent = safe_fetch(db.get_all_crimes)[:5]
    show_table(recent, "No crimes registered yet.")


# PLACEHOLDER PAGES  
# CRIMINAL MANAGEMENT
def criminals_page():
    st.header("👤 Criminal Management")
    show_flash()
    tab_view, tab_add, tab_search, tab_update, tab_delete = st.tabs(
        ["View All", "Add", "Search", "Update", "Delete"])

    #  VIEW ALL
    with tab_view:
        show_table(safe_fetch(db.get_all_criminals), "No criminals found.")

    #  ADD 
    with tab_add:
        with st.form("add_criminal_form", clear_on_submit=True):
            name = st.text_input("Name *")
            dob_known = st.checkbox("Date of birth known", value=True)
            dob = st.date_input("Date of birth", value=date(1990, 1, 1),
                                min_value=date(1900, 1, 1), max_value=date.today())
            gender = st.selectbox("Gender", db.GENDERS)
            address = st.text_input("Address")
            phone = st.text_input("Phone")
            submitted = st.form_submit_button("Add Criminal")
        if submitted:
            if not name.strip():
                st.error("Name is required.")
            elif not valid_phone(phone):
                st.error(PHONE_ERROR)
            else:
                try:
                    new_id = db.add_criminal(name, dob if dob_known else None,
                                             gender, address, phone)
                    flash(f"Criminal added successfully (ID {new_id}).")
                    st.rerun()
                except DatabaseError as e:
                    st.error(str(e))

    # SEARCH
    with tab_search:
        keyword = st.text_input("Search by ID, name, address or phone",
                                key="search_criminal")
        if keyword.strip():
            show_table(safe_fetch(db.search_criminals, keyword),
                       "No matching criminals found.")
        else:
            st.caption("Type something to search.")

    # UPDATE 
    with tab_update:
        rows = safe_fetch(db.get_all_criminals)
        if not rows:
            st.info("No criminals to update.")
        else:
            rec = pick_record(rows, "criminal_id",
                              lambda r: f"{r['criminal_id']} - {r['name']}",
                              "update_criminal_select", "Select criminal to update")
            cid = rec["criminal_id"]
            # the form key contains the id, so the fields refresh when you pick another record
            with st.form(f"update_criminal_form_{cid}"):
                name = st.text_input("Name *", value=rec["name"])
                dob_known = st.checkbox("Date of birth known",
                                        value=rec["date_of_birth"] is not None)
                dob = st.date_input("Date of birth",
                                    value=rec["date_of_birth"] or date(1990, 1, 1),
                                    min_value=date(1900, 1, 1), max_value=date.today())
                gender = st.selectbox("Gender", db.GENDERS,
                                      index=index_of(db.GENDERS, rec["gender"]))
                address = st.text_input("Address", value=rec["address"] or "")
                phone = st.text_input("Phone", value=rec["phone"] or "")
                submitted = st.form_submit_button("Update Criminal")
            if submitted:
                if not name.strip():
                    st.error("Name is required.")
                elif not valid_phone(phone):
                    st.error(PHONE_ERROR)
                else:
                    try:
                        db.update_criminal(cid, name, dob if dob_known else None,
                                           gender, address, phone)
                        flash(f"Criminal {cid} updated successfully.")
                        st.rerun()
                    except DatabaseError as e:
                        st.error(str(e))

    # DELETE
    with tab_delete:
        rows = safe_fetch(db.get_all_criminals)
        if not rows:
            st.info("No criminals to delete.")
        else:
            rec = pick_record(rows, "criminal_id",
                              lambda r: f"{r['criminal_id']} - {r['name']}",
                              "delete_criminal_select", "Select criminal to delete")
            cid = rec["criminal_id"]
            show_table([rec])
            confirm = st.checkbox("I confirm I want to delete this criminal",
                                  key=f"confirm_delete_criminal_{cid}")
            if st.button("Delete Criminal", type="primary",
                         key=f"delete_criminal_btn_{cid}"):
                if not confirm:
                    st.warning("Please tick the confirmation box first.")
                else:
                    try:
                        db.delete_criminal(cid)
                        flash(f"Criminal {cid} deleted.")
                        st.rerun()
                    except DatabaseError as e:
                        st.error(str(e))


# VICTIM MANAGEMENT
def victims_page():
    st.header("🧑 Victim Management")
    show_flash()
    tab_view, tab_add, tab_search, tab_update, tab_delete = st.tabs(
        ["View All", "Add", "Search", "Update", "Delete"])

    #  VIEW ALL 
    with tab_view:
        show_table(safe_fetch(db.get_all_victims), "No victims found.")

    #  ADD 
    with tab_add:
        with st.form("add_victim_form", clear_on_submit=True):
            name = st.text_input("Name *")
            age = st.number_input("Age", min_value=1, max_value=119, value=30, step=1)
            gender = st.selectbox("Gender", db.GENDERS)
            address = st.text_input("Address")
            phone = st.text_input("Phone")
            submitted = st.form_submit_button("Add Victim")
        if submitted:
            if not name.strip():
                st.error("Name is required.")
            elif not valid_phone(phone):
                st.error(PHONE_ERROR)
            else:
                try:
                    new_id = db.add_victim(name, int(age), gender, address, phone)
                    flash(f"Victim added successfully (ID {new_id}).")
                    st.rerun()
                except DatabaseError as e:
                    st.error(str(e))

    #  SEARCH
    with tab_search:
        keyword = st.text_input("Search by ID, name, address or phone",
                                key="search_victim")
        if keyword.strip():
            show_table(safe_fetch(db.search_victims, keyword),
                       "No matching victims found.")
        else:
            st.caption("Type something to search.")

    # UPDATE 
    with tab_update:
        rows = safe_fetch(db.get_all_victims)
        if not rows:
            st.info("No victims to update.")
        else:
            rec = pick_record(rows, "victim_id",
                              lambda r: f"{r['victim_id']} - {r['name']}",
                              "update_victim_select", "Select victim to update")
            vid = rec["victim_id"]
            with st.form(f"update_victim_form_{vid}"):
                name = st.text_input("Name *", value=rec["name"])
                age = st.number_input("Age", min_value=1, max_value=119,
                                      value=int(rec["age"] or 30), step=1)
                gender = st.selectbox("Gender", db.GENDERS,
                                      index=index_of(db.GENDERS, rec["gender"]))
                address = st.text_input("Address", value=rec["address"] or "")
                phone = st.text_input("Phone", value=rec["phone"] or "")
                submitted = st.form_submit_button("Update Victim")
            if submitted:
                if not name.strip():
                    st.error("Name is required.")
                elif not valid_phone(phone):
                    st.error(PHONE_ERROR)
                else:
                    try:
                        db.update_victim(vid, name, int(age), gender, address, phone)
                        flash(f"Victim {vid} updated successfully.")
                        st.rerun()
                    except DatabaseError as e:
                        st.error(str(e))

    # DELETE
    with tab_delete:
        rows = safe_fetch(db.get_all_victims)
        if not rows:
            st.info("No victims to delete.")
        else:
            rec = pick_record(rows, "victim_id",
                              lambda r: f"{r['victim_id']} - {r['name']}",
                              "delete_victim_select", "Select victim to delete")
            vid = rec["victim_id"]
            show_table([rec])
            confirm = st.checkbox("I confirm I want to delete this victim",
                                  key=f"confirm_delete_victim_{vid}")
            if st.button("Delete Victim", type="primary",
                         key=f"delete_victim_btn_{vid}"):
                if not confirm:
                    st.warning("Please tick the confirmation box first.")
                else:
                    try:
                        db.delete_victim(vid)
                        flash(f"Victim {vid} deleted.")
                        st.rerun()
                    except DatabaseError as e:
                        st.error(str(e))


# POLICE OFFICER MANAGEMENT
def officers_page():
    st.header("👮 Police Officer Management")
    show_flash()
    tab_view, tab_add, tab_search, tab_update, tab_delete, tab_reassign = st.tabs(
        ["View All", "Add", "Search", "Update", "Delete", "Reassign Work"])

    #  VIEW ALL
    with tab_view:
        show_table(safe_fetch(db.get_all_officers), "No officers found.")

    # ADD 
    with tab_add:
        with st.form("add_officer_form", clear_on_submit=True):
            name = st.text_input("Name *")
            rank = st.text_input("Rank * (e.g. Inspector, Sub-Inspector)")
            phone = st.text_input("Phone")
            station = st.text_input("Police station *")
            submitted = st.form_submit_button("Add Officer")
        if submitted:
            if not name.strip() or not rank.strip() or not station.strip():
                st.error("Name, rank and police station are required.")
            elif not valid_phone(phone):
                st.error(PHONE_ERROR)
            else:
                try:
                    new_id = db.add_officer(name, rank, phone, station)
                    flash(f"Officer added successfully (ID {new_id}).")
                    st.rerun()
                except DatabaseError as e:
                    st.error(str(e))

    #  SEARCH
    with tab_search:
        keyword = st.text_input("Search by ID, name, rank, station or phone",
                                key="search_officer")
        if keyword.strip():
            show_table(safe_fetch(db.search_officers, keyword),
                       "No matching officers found.")
        else:
            st.caption("Type something to search.")

    #  UPDATE
    with tab_update:
        rows = safe_fetch(db.get_all_officers)
        if not rows:
            st.info("No officers to update.")
        else:
            rec = pick_record(rows, "officer_id",
                              lambda r: f"{r['officer_id']} - {r['name']} ({r['rank']})",
                              "update_officer_select", "Select officer to update")
            oid = rec["officer_id"]
            with st.form(f"update_officer_form_{oid}"):
                name = st.text_input("Name *", value=rec["name"])
                rank = st.text_input("Rank *", value=rec["rank"])
                phone = st.text_input("Phone", value=rec["phone"] or "")
                station = st.text_input("Police station *", value=rec["police_station"])
                submitted = st.form_submit_button("Update Officer")
            if submitted:
                if not name.strip() or not rank.strip() or not station.strip():
                    st.error("Name, rank and police station are required.")
                elif not valid_phone(phone):
                    st.error(PHONE_ERROR)
                else:
                    try:
                        db.update_officer(oid, name, rank, phone, station)
                        flash(f"Officer {oid} updated successfully.")
                        st.rerun()
                    except DatabaseError as e:
                        st.error(str(e))

    #DELETE
    with tab_delete:
        rows = safe_fetch(db.get_all_officers)
        if not rows:
            st.info("No officers to delete.")
        else:
            rec = pick_record(rows, "officer_id",
                              lambda r: f"{r['officer_id']} - {r['name']} ({r['rank']})",
                              "delete_officer_select", "Select officer to delete")
            oid = rec["officer_id"]
            show_table([rec])
            confirm = st.checkbox("I confirm I want to delete this officer",
                                  key=f"confirm_delete_officer_{oid}")
            if st.button("Delete Officer", type="primary",
                         key=f"delete_officer_btn_{oid}"):
                if not confirm:
                    st.warning("Please tick the confirmation box first.")
                else:
                    try:
                        db.delete_officer(oid)
                        flash(f"Officer {oid} deleted.")
                        st.rerun()
                    except DatabaseError as e:
                        st.error(str(e))

    #REASSIGN WORK
    with tab_reassign:
        st.caption("Moves ALL crimes and cases from one officer to another. "
                   "Both updates happen in a single transaction: either both "
                   "succeed or neither is saved.")
        options = option_map(safe_fetch(db.get_officer_options))
        if len(options) < 2:
            st.info("You need at least two officers to reassign work.")
        else:
            labels = list(options.keys())
            from_label = st.selectbox("From officer", labels, key="reassign_from")
            to_label = st.selectbox("To officer", labels, index=1, key="reassign_to")
            if st.button("Reassign All Work", key="reassign_btn"):
                try:
                    crimes_moved, cases_moved = db.reassign_officer_work(
                        options[from_label], options[to_label])
                    flash(f"Moved {crimes_moved} crime(s) and {cases_moved} case(s).")
                    st.rerun()
                except DatabaseError as e:
                    st.error(str(e))


# CRIME MANAGEMENT
def crimes_page():
    st.header("🚨 Crime Management")
    show_flash()
    tab_view, tab_add, tab_search, tab_update, tab_delete = st.tabs(
        ["View All", "Register Crime", "Search", "Update", "Delete"])

    # Dropdown data comes straight from the database
    criminal_map = {NO_CRIMINAL: None, **option_map(safe_fetch(db.get_criminal_options))}
    victim_map = option_map(safe_fetch(db.get_victim_options))
    officer_map = option_map(safe_fetch(db.get_officer_options))

    #  VIEW ALL
    with tab_view:
        show_table(safe_fetch(db.get_all_crimes), "No crimes found.")

    # REGISTER 
    with tab_add:
        if not victim_map or not officer_map:
            st.warning("Add at least one victim and one police officer first.")
        else:
            with st.form("add_crime_form", clear_on_submit=True):
                crime_type = st.selectbox("Crime type *", db.CRIME_TYPES)
                crime_date = st.date_input("Crime date *", value=date.today(),
                                           max_value=date.today())
                location = st.text_input("Location *")
                description = st.text_area("Description")
                criminal_label = st.selectbox("Criminal", list(criminal_map.keys()))
                victim_label = st.selectbox("Victim *", list(victim_map.keys()))
                officer_label = st.selectbox("Investigating officer *",
                                             list(officer_map.keys()))
                submitted = st.form_submit_button("Register Crime")
            if submitted:
                if not location.strip():
                    st.error("Location is required.")
                else:
                    try:
                        new_id = db.add_crime(
                            crime_type, crime_date, location, description,
                            criminal_map[criminal_label],
                            victim_map[victim_label],
                            officer_map[officer_label])
                        flash(f"Crime registered successfully (ID {new_id}).")
                        st.rerun()
                    except DatabaseError as e:
                        st.error(str(e))

    # SEARCH
    with tab_search:
        keyword = st.text_input(
            "Search by ID, type, location, description, criminal, victim or officer",
            key="search_crime")
        if keyword.strip():
            show_table(safe_fetch(db.search_crimes, keyword),
                       "No matching crimes found.")
        else:
            st.caption("Type something to search.")

    #  UPDATE 
    with tab_update:
        rows = safe_fetch(db.get_all_crimes)
        if not rows:
            st.info("No crimes to update.")
        else:
            rec = pick_record(
                rows, "crime_id",
                lambda r: f"{r['crime_id']} - {r['crime_type']} ({r['location']})",
                "update_crime_select", "Select crime to update")
            crid = rec["crime_id"]

            types = list(db.CRIME_TYPES)
            if rec["crime_type"] not in types:     
                types.append(rec["crime_type"])

            with st.form(f"update_crime_form_{crid}"):
                crime_type = st.selectbox("Crime type *", types,
                                          index=index_of(types, rec["crime_type"]))
                crime_date = st.date_input("Crime date *", value=rec["crime_date"],
                                           max_value=date.today())
                location = st.text_input("Location *", value=rec["location"])
                description = st.text_area("Description", value=rec["description"] or "")
                criminal_label = st.selectbox(
                    "Criminal", list(criminal_map.keys()),
                    index=index_of_value(criminal_map, rec["criminal_id"]))
                victim_label = st.selectbox(
                    "Victim *", list(victim_map.keys()),
                    index=index_of_value(victim_map, rec["victim_id"]))
                officer_label = st.selectbox(
                    "Investigating officer *", list(officer_map.keys()),
                    index=index_of_value(officer_map, rec["officer_id"]))
                submitted = st.form_submit_button("Update Crime")
            if submitted:
                if not location.strip():
                    st.error("Location is required.")
                else:
                    try:
                        db.update_crime(
                            crid, crime_type, crime_date, location, description,
                            criminal_map[criminal_label],
                            victim_map[victim_label],
                            officer_map[officer_label])
                        flash(f"Crime {crid} updated successfully.")
                        st.rerun()
                    except DatabaseError as e:
                        st.error(str(e))

    #  DELETE
    with tab_delete:
        rows = safe_fetch(db.get_all_crimes)
        if not rows:
            st.info("No crimes to delete.")
        else:
            rec = pick_record(
                rows, "crime_id",
                lambda r: f"{r['crime_id']} - {r['crime_type']} ({r['location']})",
                "delete_crime_select", "Select crime to delete")
            crid = rec["crime_id"]
            show_table([rec])

            linked_cases = [c for c in safe_fetch(db.get_all_cases)
                            if c["crime_id"] == crid]
            if linked_cases:
                st.warning(f"This crime has {len(linked_cases)} linked case(s). "
                           "Deleting the crime will ALSO delete those cases.")

            confirm = st.checkbox("I confirm I want to delete this crime",
                                  key=f"confirm_delete_crime_{crid}")
            if st.button("Delete Crime", type="primary",
                         key=f"delete_crime_btn_{crid}"):
                if not confirm:
                    st.warning("Please tick the confirmation box first.")
                else:
                    try:
                        db.delete_crime(crid)
                        flash(f"Crime {crid} deleted.")
                        st.rerun()
                    except DatabaseError as e:
                        st.error(str(e))


# CASE MANAGEMENT
def cases_page():
    st.header("📁 Case Management")
    show_flash()
    tab_view, tab_add, tab_search, tab_status, tab_edit, tab_delete = st.tabs(
        ["View All", "Register Case", "Search", "Update Status",
         "Edit Details", "Delete"])

    crime_map = option_map(safe_fetch(db.get_crime_options))
    officer_map = option_map(safe_fetch(db.get_officer_options))

    #VIEW ALL 
    with tab_view:
        show_table(safe_fetch(db.get_all_cases), "No cases found.")

    #  REGISTER
    with tab_add:
        if not crime_map or not officer_map:
            st.warning("Register at least one crime and one police officer first.")
        else:
            with st.form("add_case_form", clear_on_submit=True):
                case_number = st.text_input("Case number *", value=next_case_number())
                crime_label = st.selectbox("Related crime *", list(crime_map.keys()))
                officer_label = st.selectbox("Police officer *", list(officer_map.keys()))
                filing_date = st.date_input("Filing date *", value=date.today(),
                                            max_value=date.today())
                status = st.selectbox("Status", db.CASE_STATUSES)
                description = st.text_area("Description")
                submitted = st.form_submit_button("Register Case")
            if submitted:
                if not case_number.strip():
                    st.error("Case number is required.")
                else:
                    try:
                        new_id = db.add_case(case_number, crime_map[crime_label],
                                             officer_map[officer_label], filing_date,
                                             status, description)
                        flash(f"Case registered successfully (ID {new_id}).")
                        st.rerun()
                    except DatabaseError as e:
                        st.error(str(e))

    #  SEARCH
    with tab_search:
        keyword = st.text_input(
            "Search by ID, case number, status, crime type, officer or description",
            key="search_case")
        if keyword.strip():
            show_table(safe_fetch(db.search_cases, keyword),
                       "No matching cases found.")
        else:
            st.caption("Type something to search.")

    # UPDATE STATUS 
    with tab_status:
        rows = safe_fetch(db.get_all_cases)
        if not rows:
            st.info("No cases to update.")
        else:
            rec = pick_record(
                rows, "case_id",
                lambda r: f"{r['case_number']} - {r['crime_type']} [{r['status']}]",
                "status_case_select", "Select case")
            cid = rec["case_id"]
            st.write(f"Current status: **{rec['status']}**")
            with st.form(f"update_status_form_{cid}"):
                new_status = st.selectbox("New status", db.CASE_STATUSES,
                                          index=index_of(db.CASE_STATUSES, rec["status"]))
                submitted = st.form_submit_button("Update Status")
            if submitted:
                try:
                    db.update_case_status(cid, new_status)
                    flash(f"Case {rec['case_number']} is now '{new_status}'.")
                    st.rerun()
                except DatabaseError as e:
                    st.error(str(e))

    #  EDIT DETAILS 
    with tab_edit:
        rows = safe_fetch(db.get_all_cases)
        if not rows:
            st.info("No cases to edit.")
        else:
            rec = pick_record(
                rows, "case_id",
                lambda r: f"{r['case_number']} - {r['crime_type']}",
                "edit_case_select", "Select case to edit")
            cid = rec["case_id"]
            with st.form(f"edit_case_form_{cid}"):
                case_number = st.text_input("Case number *", value=rec["case_number"])
                crime_label = st.selectbox(
                    "Related crime *", list(crime_map.keys()),
                    index=index_of_value(crime_map, rec["crime_id"]))
                officer_label = st.selectbox(
                    "Police officer *", list(officer_map.keys()),
                    index=index_of_value(officer_map, rec["officer_id"]))
                filing_date = st.date_input("Filing date *", value=rec["filing_date"],
                                            max_value=date.today())
                status = st.selectbox("Status", db.CASE_STATUSES,
                                      index=index_of(db.CASE_STATUSES, rec["status"]))
                description = st.text_area("Description", value=rec["description"] or "")
                submitted = st.form_submit_button("Save Changes")
            if submitted:
                if not case_number.strip():
                    st.error("Case number is required.")
                else:
                    try:
                        db.update_case(cid, case_number, crime_map[crime_label],
                                       officer_map[officer_label], filing_date,
                                       status, description)
                        flash(f"Case {cid} updated successfully.")
                        st.rerun()
                    except DatabaseError as e:
                        st.error(str(e))

    #  DELETE 
    with tab_delete:
        rows = safe_fetch(db.get_all_cases)
        if not rows:
            st.info("No cases to delete.")
        else:
            rec = pick_record(
                rows, "case_id",
                lambda r: f"{r['case_number']} - {r['crime_type']} [{r['status']}]",
                "delete_case_select", "Select case to delete")
            cid = rec["case_id"]
            show_table([rec])
            confirm = st.checkbox("I confirm I want to delete this case",
                                  key=f"confirm_delete_case_{cid}")
            if st.button("Delete Case", type="primary", key=f"delete_case_btn_{cid}"):
                if not confirm:
                    st.warning("Please tick the confirmation box first.")
                else:
                    try:
                        db.delete_case(cid)
                        flash(f"Case {rec['case_number']} deleted.")
                        st.rerun()
                    except DatabaseError as e:
                        st.error(str(e))


# REPORTS
def report_section(title, sql_note, rows, index_col, value_col):
    """Show one report: a table on the left and a bar chart on the right."""
    st.subheader(title)
    st.caption(f"SQL used: {sql_note}")
    if not rows:
        st.info("No data available for this report.")
        return
    df = pd.DataFrame(rows)
    left, right = st.columns(2)
    with left:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"{len(df)} row(s)")
    with right:
        chart_data = df.set_index(index_col)[[value_col]].astype(float)
        st.bar_chart(chart_data)


def reports_page():
    st.header("📈 Reports")
    show_flash()

    tabs = st.tabs([
        "1. Crimes by Type",
        "2. Cases by Status",
        "3. Crimes per Officer",
        "4. Repeat Criminals",
        "5. Cases per Officer",
        "Extra: Avg Victim Age",
        "Extra: Crimes Without Case",
    ])

    with tabs[0]:
        report_section(
            "Crimes by Crime Type",
            "GROUP BY + COUNT",
            safe_fetch(db.report_crimes_by_type),
            "crime_type", "total_crimes")

    with tabs[1]:
        report_section(
            "Cases by Status",
            "GROUP BY + COUNT",
            safe_fetch(db.report_cases_by_status),
            "status", "total_cases")

    with tabs[2]:
        report_section(
            "Crimes Handled by Each Police Officer",
            "LEFT JOIN + GROUP BY + COUNT",
            safe_fetch(db.report_crimes_per_officer),
            "officer_name", "crimes_handled")

    with tabs[3]:
        report_section(
            "Criminals Involved in Multiple Crimes",
            "INNER JOIN + GROUP BY + HAVING COUNT(...) > 1",
            safe_fetch(db.report_repeat_criminals),
            "criminal_name", "total_crimes")

    with tabs[4]:
        report_section(
            "Number of Cases Handled by Each Officer",
            "LEFT JOIN + GROUP BY + COUNT",
            safe_fetch(db.report_cases_per_officer),
            "officer_name", "cases_handled")

    with tabs[5]:
        report_section(
            "Average Victim Age by Crime Type",
            "INNER JOIN + GROUP BY + AVG",
            safe_fetch(db.report_avg_victim_age_by_crime_type),
            "crime_type", "average_victim_age")

    with tabs[6]:
        st.subheader("Crimes That Have No Case Registered Yet")
        st.caption("SQL used: subquery (NOT IN)")
        rows = safe_fetch(db.report_crimes_without_case)
        show_table(rows, "Every crime has a case.")


# SIDEBAR NAVIGATION
PAGES = {
    "Dashboard": dashboard_page,
    "Criminal Management": criminals_page,
    "Victim Management": victims_page,
    "Police Officer Management": officers_page,
    "Crime Management": crimes_page,
    "Case Management": cases_page,
    "Reports": reports_page,
}

st.sidebar.title("🚔 CDMS")
st.sidebar.caption("Crime Database Management System")
selected_page = st.sidebar.radio("Navigation", list(PAGES.keys()))
st.sidebar.divider()
st.sidebar.caption("Python • PostgreSQL • Streamlit")

# Run the selected page
PAGES[selected_page]()