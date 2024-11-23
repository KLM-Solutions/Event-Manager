import streamlit as st
from datetime import datetime, time
import json
import os
import time as tm
from plyer import notification  # For desktop notifications
import schedule
import threading
import pytz


# Initialize session state if not exists
if 'medications' not in st.session_state:
    st.session_state.medications = {}

class MedicationManager:
    def __init__(self):
        self.medications = st.session_state.medications
        self.load_medications()

    # Initialize session state
if 'medications' not in st.session_state:
    st.session_state.medications = {}
if 'notifications_enabled' not in st.session_state:
    st.session_state.notifications_enabled = False

class MedicationManager:
    def __init__(self):
        self.medications = st.session_state.medications
        self.load_medications()

    def add_medication(self, name, dosage, time, frequency, notes=None, reminder=True):
        med_id = f"med_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        medication = {
            "id": med_id,
            "name": name,
            "dosage": dosage,
            "time": time,
            "frequency": frequency,
            "notes": notes,
            "status": "pending",
            "reminder": reminder,
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

def send_notification(title, message):
    try:
        notification.notify(
            title=title,
            message=message,
            app_icon=None,  # e.g. 'C:\\icon_32x32.ico'
            timeout=10,
        )
    except Exception as e:
        st.error(f"Notification error: {e}")

def check_medication_times():
    while True:
        if st.session_state.notifications_enabled:
            current_time = datetime.now().time()
            for med in st.session_state.medications.values():
                if med['status'] == 'pending' and med['reminder']:
                    med_time = datetime.strptime(med['time'], "%H:%M").time()
                    if (current_time.hour == med_time.hour and 
                        current_time.minute == med_time.minute):
                        send_notification(
                            "Medication Reminder",
                            f"Time to take {med['name']} - {med['dosage']}"
                        )
        tm.sleep(60)  # Check every minute

# Start notification thread
notification_thread = threading.Thread(target=check_medication_times, daemon=True)
notification_thread.start()

def main():
    st.title("Medication Manager")

    # Sidebar for navigation and settings
    page = st.sidebar.radio("Navigation", ["View Medications", "Add Medication", "Settings"])

    if page == "View Medications":
        show_medications()
    elif page == "Add Medication":
        add_medication_form()
    else:
        show_settings()

def show_settings():
    st.header("Notification Settings")
    
    # Enable/Disable notifications
    notifications_enabled = st.toggle(
        "Enable Notifications",
        value=st.session_state.notifications_enabled
    )
    
    if notifications_enabled != st.session_state.notifications_enabled:
        st.session_state.notifications_enabled = notifications_enabled
        if notifications_enabled:
            st.success("Notifications enabled!")
        else:
            st.warning("Notifications disabled!")

    # Time zone selection
    time_zones = pytz.all_timezones
    selected_timezone = st.selectbox(
        "Select your timezone",
        time_zones,
        index=time_zones.index('UTC')
    )
    
    st.info("""
    Notification Tips:
    - Make sure to allow browser notifications
    - Notifications will only work when the app is running
    - You'll receive notifications at the exact medication times
    """)

def add_medication_form():
    st.header("Add New Medication")

    with st.form("add_medication_form"):
        name = st.text_input("Medication Name")
        dosage = st.text_input("Dosage")
        time = st.time_input("Time")
        frequency = st.text_input("Frequency")
        notes = st.text_area("Notes")
        reminder = st.checkbox("Enable reminder for this medication", value=True)

        submitted = st.form_submit_button("Add Medication")
        if submitted:
            if name and dosage and time and frequency:
                medication_manager.add_medication(
                    name=name,
                    dosage=dosage,
                    time=time.strftime("%H:%M"),
                    frequency=frequency,
                    notes=notes,
                    reminder=reminder
                )
                st.success("Medication added successfully!")
                st.rerun()
            else:
                st.error("Please fill in all required fields.")

def show_medications():
    # Filter options
    col1, col2 = st.columns([2, 1])
    with col1:
        filter_type = st.selectbox(
            "Filter medications",
            ["today", "completed", "pending", "all"],
            key="filter"
        )
    
    with col2:
        st.write("")
        st.write("")
        if st.button("🔔 Test Notification"):
            send_notification(
                "Test Notification",
                "This is a test notification from Medication Manager!"
            )

    medications = medication_manager.get_medications(filter_type)

    if not medications:
        st.info("No medications found.")
        return

    for med in medications:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.write(f"**{med['name']}** - {med['dosage']}")
            st.write(f"Time: {med['time']} | Frequency: {med['frequency']}")
            if med.get('notes'):
                st.write(f"Notes: {med['notes']}")
            if med.get('reminder'):
                st.write("🔔 Reminders enabled")

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

        with col4:
            if st.button(
                "🔕" if med.get('reminder') else "🔔",
                key=f"reminder_{med['id']}"
            ):
                medication_manager.update_medication(
                    med['id'],
                    {"reminder": not med.get('reminder', True)}
                )
                st.rerun()

        st.divider()

if __name__ == "__main__":
    medication_manager = MedicationManager()
    main()
