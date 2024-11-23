import streamlit as st
from datetime import datetime
import json
import os

# Initialize session state if not exists
if 'medications' not in st.session_state:
    st.session_state.medications = {}

class MedicationManager:
    def __init__(self):
        self.medications = st.session_state.medications
        self.load_medications()

    def add_medication(self, name, dosage, time, frequency, notes=None):
        med_id = f"med_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        medication = {
            "id": med_id,
            "name": name,
            "dosage": dosage,
            "time": time,
            "frequency": frequency,
            "notes": notes,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        self.medications[med_id] = medication
        st.session_state.medications = self.medications
        return medication

    def get_medications(self, filter_type="today"):
        if filter_type == "all":
            return list(self.medications.values())
        
        filtered_meds = []
        for med in self.medications.values():
            if filter_type == "today":
                filtered_meds.append(med)
            elif filter_type == "completed":
                if med["status"] == "completed":
                    filtered_meds.append(med)
            elif filter_type == "pending":
                if med["status"] == "pending":
                    filtered_meds.append(med)
        return filtered_meds

    def update_medication(self, med_id, updates):
        if med_id in self.medications:
            self.medications[med_id].update(updates)
            st.session_state.medications = self.medications
            return self.medications[med_id]
        return None

    def delete_medication(self, med_id):
        if med_id in self.medications:
            del self.medications[med_id]
            st.session_state.medications = self.medications
            return True
        return False

    def save_medications(self):
        # Optional: Save to file if needed
        pass

    def load_medications(self):
        # Optional: Load from file if needed
        pass

# Initialize the medication manager
medication_manager = MedicationManager()

def main():
    st.title("Medication Manager")

    # Sidebar for navigation
    page = st.sidebar.radio("Navigation", ["View Medications", "Add Medication"])

    if page == "View Medications":
        show_medications()
    else:
        add_medication_form()

def show_medications():
    # Filter options
    filter_type = st.selectbox(
        "Filter medications",
        ["today", "completed", "pending", "all"],
        key="filter"
    )

    medications = medication_manager.get_medications(filter_type)

    if not medications:
        st.info("No medications found.")
        return

    for med in medications:
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"**{med['name']}** - {med['dosage']} - {med['time']}")
            if med.get('notes'):
                st.write(f"Notes: {med['notes']}")

        with col2:
            if st.button(
                "Mark Complete" if med['status'] == 'pending' else "Mark Pending",
                key=f"status_{med['id']}"
            ):
                new_status = "completed" if med['status'] == 'pending' else 'pending'
                medication_manager.update_medication(med['id'], {"status": new_status})
                st.rerun()

        with col3:
            if st.button("Delete", key=f"delete_{med['id']}"):
                medication_manager.delete_medication(med['id'])
                st.rerun()

        st.divider()

def add_medication_form():
    st.header("Add New Medication")

    with st.form("add_medication_form"):
        name = st.text_input("Medication Name")
        dosage = st.text_input("Dosage")
        time = st.time_input("Time")
        frequency = st.text_input("Frequency")
        notes = st.text_area("Notes")

        submitted = st.form_submit_button("Add Medication")
        if submitted:
            if name and dosage and time and frequency:
                medication_manager.add_medication(
                    name=name,
                    dosage=dosage,
                    time=time.strftime("%H:%M"),
                    frequency=frequency,
                    notes=notes
                )
                st.success("Medication added successfully!")
                st.rerun()
            else:
                st.error("Please fill in all required fields.")

if __name__ == "__main__":
    main()
