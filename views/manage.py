"""Manage categories and subjects."""

import html

import streamlit as st

import db
from styles import narrow_page
from ui import run_action, show_flash

SUBJECT_COLUMNS = [4, 3, 2, 2]

narrow_page()


st.title("Manage")

show_flash()

categories = db.list_categories()
subjects = db.list_subjects()
archived_categories = [c for c in db.list_categories(include_archived=True) if c["archived"]]
archived_subjects = [s for s in db.list_subjects(include_archived=True) if s["archived"]]
all_categories = {c["id"]: c for c in db.list_categories(include_archived=True)}
active_count = {c["id"]: 0 for c in categories}
for s in subjects:
    if s["category_id"] in active_count:
        active_count[s["category_id"]] += 1

# Categories

st.header("Categories")

with st.form("add_category", clear_on_submit=True, border=False):
    name_col, button_col = st.columns([5, 2], vertical_alignment="bottom")
    new_category = name_col.text_input("New category", placeholder="e.g. School, Work, Hobby")
    if button_col.form_submit_button("Add category", type="primary", use_container_width=True):
        run_action(lambda: db.create_category(new_category), f"Added category '{new_category.strip()}'.")

if not categories:
    st.markdown(
        '<p class="muted">No categories yet. Add one above, then give it some subjects.</p>',
        unsafe_allow_html=True,
    )
else:
    head = st.columns([5, 2, 2, 2])
    head[0].markdown('<span class="board-head">Category</span>', unsafe_allow_html=True)
    head[1].markdown('<span class="board-head">Subjects</span>', unsafe_allow_html=True)
    for category in categories:
        with st.form(f"category_{category['id']}", border=False):
            cols = st.columns([5, 2, 2, 2])
            name = cols[0].text_input(
                f"Name of {category['name']}", value=category["name"], label_visibility="collapsed"
            )
            count = active_count[category["id"]]
            noun = "subject" if count == 1 else "subjects"
            cols[1].markdown(f'<div class="row-note">{count} {noun}</div>', unsafe_allow_html=True)
            rename = cols[2].form_submit_button("Rename", use_container_width=True)
            archive = cols[3].form_submit_button(
                "Archive", use_container_width=True, disabled=count > 0, help=(
                    "Archive or move this category's subjects first." if count else None
                ),
            )
            if rename:
                run_action(lambda: db.rename_category(category["id"], name), "Category renamed.")
            if archive:
                run_action(lambda: db.archive_category(category["id"]), f"Archived '{category['name']}'.")

# Subjects

st.header("Subjects")

if not categories:
    st.markdown('<p class="muted">Create a category first, then add subjects to it.</p>', unsafe_allow_html=True)
else:
    category_ids = [c["id"] for c in categories]
    with st.form("add_subject", clear_on_submit=True, border=False):
        name_col, category_col, button_col = st.columns([4, 3, 2], vertical_alignment="bottom")
        new_subject = name_col.text_input("New subject", placeholder="e.g. SAT Math")
        new_subject_category = category_col.selectbox(
            "Category", category_ids, format_func=lambda cid: all_categories[cid]["name"]
        )
        if button_col.form_submit_button("Add subject", type="primary", use_container_width=True):
            run_action(
                lambda: db.create_subject(new_subject, new_subject_category),
                f"Added subject '{new_subject.strip()}'.",
            )

    if not subjects:
        st.markdown(
            '<p class="muted">No subjects yet. Add the things you study or work on above.</p>',
            unsafe_allow_html=True,
        )
    else:
        head = st.columns(SUBJECT_COLUMNS)
        head[0].markdown('<span class="board-head">Subject</span>', unsafe_allow_html=True)
        head[1].markdown('<span class="board-head">Category</span>', unsafe_allow_html=True)
        ordered = sorted(subjects, key=lambda s: (all_categories[s["category_id"]]["name"].lower(), s["name"].lower()))
        for subject in ordered:
            options = list(category_ids)
            if subject["category_id"] not in options:
                options.append(subject["category_id"])
            with st.form(f"subject_{subject['id']}", border=False):
                cols = st.columns(SUBJECT_COLUMNS)
                name = cols[0].text_input(
                    f"Name of {subject['name']}", value=subject["name"], label_visibility="collapsed"
                )
                category_id = cols[1].selectbox(
                    f"Category of {subject['name']}",
                    options,
                    index=options.index(subject["category_id"]),
                    format_func=lambda cid: all_categories[cid]["name"],
                    label_visibility="collapsed",
                )
                save = cols[2].form_submit_button("Save", use_container_width=True)
                archive = cols[3].form_submit_button("Archive", use_container_width=True)

                def apply_changes(subject=subject, name=name, category_id=category_id):
                    if name.strip() != subject["name"]:
                        db.rename_subject(subject["id"], name)
                    if category_id != subject["category_id"]:
                        db.recategorize_subject(subject["id"], category_id)

                if save:
                    run_action(apply_changes, "Subject updated.")
                if archive:
                    run_action(lambda: db.archive_subject(subject["id"]), f"Archived '{subject['name']}'.")

# Archived

archived_total = len(archived_categories) + len(archived_subjects)
if archived_total:
    with st.expander(f"Archived ({archived_total})"):
        st.markdown(
            '<p class="muted">Archived items are hidden from pickers. Their logged sessions are kept.</p>',
            unsafe_allow_html=True,
        )
        for category in archived_categories:
            cols = st.columns([7, 2], vertical_alignment="center")
            cols[0].markdown(
                f"{html.escape(category['name'])} <span class='muted'>(category)</span>", unsafe_allow_html=True
            )
            if cols[1].button("Restore", key=f"restore_category_{category['id']}", use_container_width=True):
                run_action(lambda: db.unarchive_category(category["id"]), f"Restored '{category['name']}'.")
        for subject in archived_subjects:
            category_name = all_categories[subject["category_id"]]["name"]
            cols = st.columns([7, 2], vertical_alignment="center")
            cols[0].markdown(
                f"{html.escape(subject['name'])} <span class='muted'>({html.escape(category_name)})</span>",
                unsafe_allow_html=True,
            )
            if cols[1].button("Restore", key=f"restore_subject_{subject['id']}", use_container_width=True):
                run_action(lambda: db.unarchive_subject(subject["id"]), f"Restored '{subject['name']}'.")
