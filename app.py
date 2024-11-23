import streamlit as st
from datetime import datetime, timedelta, time
import json
import os
import time as tm
from plyer import notification
import schedule
import threading
import pytz
from win10toast import ToastNotifier

# Initialize session state
if 'medications' not in st.session_state:
    st.session_state.medications = {}
if 'notifications_enabled' not in st.session_state:
    st.session_state.notifications_enabled = False

class MedicationManager:
    def __init__(self):
        self.medications = st.session_state.medications
        self.load_medications()

    def add_medication(self, name, dosage, time, frequency, notes=None, reminder_settings=None):
        med_id = f"med_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        medication = {
            "id": med_id,
            "name": name,
            "dosage": dosage,
            "time": time,
            "frequency": frequency,
            "notes": notes,
            "status": "pending",
            "reminder_settings": reminder_settings or {"enabled": False},
            "created_at": datetime.now().isoformat()
        }
        self.medications[med_id] = medication
        st.session_state.medications = self.medications
        self.save_medications()
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
            self.save_medications()
            return self.medications[med_id]
        return None

    def delete_medication(self, med_id):
        if med_id in self.medications:
            del self.medications[med_id]
            st.session_state.medications = self.medications
            self.save_medications()
            return True
        return False

    def save_medications(self):
        try:
            with open("medications.json", "w") as f:
                json.dump(self.medications, f, indent=2)
        except Exception as e:
            st.error(f"Error saving medications: {e}")

    def load_medications(self):
        try:
            if os.path.exists("medications.json"):
                with open("medications.json", "r") as f:
                    loaded_meds = json.load(f)
                    self.medications = loaded_meds
                    st.session_state.medications = loaded_meds
        except Exception as e:
            st.error(f"Error loading medications: {e}")

def send_notification(title, message):
    try:
        notification.notify(
            title=title,
            message=message,
            app_icon=None,
            timeout=10,
        )
    except Exception as e:
        st.error(f"Notification error: {e}")

def check_medication_times():
    while True:
        if st.session_state.notifications_enabled:
            ist = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist)
            current_minute = current_time.strftime("%H:%M")
            
            for med in st.session_state.medications.values():
                if med['status'] == 'pending' and med.get('reminder_settings', {}).get('enabled'):
                    scheduled_time = med['time']
                    
                    # Main medication time check
                    if current_minute == scheduled_time:
                        send_notification(
                            "Medication Reminder",
                            f"Time to take {med['name']} - {med['dosage']}"
                        )
                    
                    # Advance reminder check
                    if med['reminder_settings'].get('remind_before', 0) > 0:
                        scheduled_dt = datetime.strptime(scheduled_time, "%H:%M")
                        advance_time = (scheduled_dt - timedelta(
                            minutes=med['reminder_settings']['remind_before']
                        )).strftime("%H:%M")
                        
                        if current_minute == advance_time:
                            send_notification(
                                "Advance Medication Reminder",
                                f"Reminder: Take {med['name']} in {med['reminder_settings']['remind_before']} minutes"
                            )
        
        tm.sleep(30)

# Start notification thread
notification_thread = threading.Thread(target=check_medication_times, daemon=True)
notification_thread.start()

def show_settings():
    st.header("Notification Settings")
    
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

    time_zones = pytz.all_timezones
    default_timezone = 'Asia/Kolkata'
    default_index = time_zones.index(default_timezone)
    
    selected_timezone = st.selectbox(
        "Select your timezone",
        time_zones,
        index=default_index,
        help="For India, use Asia/Kolkata timezone"
    )

    current_time = datetime.now(pytz.timezone(selected_timezone))
    st.write(f"Current time: **{current_time.strftime('%I:%M %p, %d %B %Y')}**")

def add_medication_form():
    st.header("Add New Medication")

    with st.form("add_medication_form"):
        name = st.text_input("Medication Name")
        dosage = st.text_input("Dosage")
        
        # Fixed time selection
        selected_time = st.time_input(
            "Select Time",
            value=time(hour=9, minute=0),  # Default to 9:00 AM
            step=60
        )
        
        # Show exact selected time
        formatted_time = selected_time.strftime("%I:%M %p")
        st.write(f"Reminder will be set for: **{formatted_time}**")

        frequency_options = [
            "Once daily",
            "Twice daily",
            "Three times daily",
            "Every 8 hours",
            "Every 12 hours",
            "Custom"
        ]
        
        frequency = st.selectbox(
            "Frequency",
            options=frequency_options
        )
        
        if frequency == "Custom":
            frequency = st.text_input(
                "Enter custom frequency",
                help="Example: Every 6 hours, Weekly, etc."
            )

        st.write("Reminder Settings")
        reminder = st.checkbox("Enable reminders", value=True)
        
        remind_before = 0
        if reminder:
            remind_before = st.slider(
                "Remind me before",
                min_value=0,
                max_value=60,
                value=5,
                step=5,
                help="Minutes before medication time"
            )

        notes = st.text_area(
            "Notes (Optional)", 
            placeholder="Example: take with food, take after meals, etc."
        )

        submitted = st.form_submit_button("Add Medication")
        if submitted:
            if name and dosage and frequency:
                # Store exact selected time
                time_str = selected_time.strftime("%H:%M")
                
                reminder_settings = {
                    "enabled": reminder,
                    "remind_before": remind_before if reminder else 0,
                    "time": time_str
                }

                medication_manager.add_medication(
                    name=name,
                    dosage=dosage,
                    time=time_str,
                    frequency=frequency,
                    notes=notes,
                    reminder_settings=reminder_settings
                )
                st.success(f"Medication added successfully! Reminder set for {formatted_time}")
                st.rerun()
            else:
                st.error("Please fill in all required fields.")

def show_medications():
    col1, col2 = st.columns([2, 1])
    with col1:
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
        
        time_24 = datetime.strptime(med['time'], "%H:%M")
        time_12 = time_24.strftime("%I:%M %p")
        
        with col1:
            st.markdown(f"""
            **{med['name']}** - {med['dosage']}
            Time: {time_12} | Frequency: {med['frequency']}
            """)
            
            if med.get('reminder_settings', {}).get('enabled'):
                reminder_info = f"🔔 Reminder set for {time_12}"
                if med['reminder_settings'].get('remind_before'):
                    reminder_info += f" (with {med['reminder_settings']['remind_before']} min advance notice)"
                st.info(reminder_info)
            
            if med.get('notes'):
                st.write(f"Notes: {med['notes']}")

        with col2:
            if st.button(
                "✓ Taken" if med['status'] == 'pending' else "↺ Reset",
                key=f"status_{med['id']}"
            ):
                new_status = "completed" if med['status'] == 'pending' else 'pending'
                medication_manager.update_medication(med['id'], {"status": new_status})
                st.rerun()

        with col3:
            if st.button("🗑️ Delete", key=f"delete_{med['id']}"):
                medication_manager.delete_medication(med['id'])
                st.rerun()

        st.divider()

def main():
    st.title("Medication Manager")
    
    page = st.sidebar.radio("Navigation", ["View Medications", "Add Medication", "Settings"])

    if page == "View Medications":
        show_medications()
    elif page == "Add Medication":
        add_medication_form()
    else:
        show_settings()

if __name__ == "__main__":
    medication_manager = MedicationManager()
    main()
