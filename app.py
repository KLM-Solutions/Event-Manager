import streamlit as st
from datetime import datetime, timedelta, time
import json
import os
import time as tm
from plyer import notification
import schedule
import threading
import pytz

# Initialize session state for storing data across reruns
if 'medications' not in st.session_state:
    st.session_state.medications = {}
if 'notifications_enabled' not in st.session_state:
    st.session_state.notifications_enabled = False

class MedicationManager:
    def __init__(self):
        self.medications = st.session_state.medications
        self.load_medications()

    def add_medication(self, name, dosage, time, frequency, notes=None, reminder_settings=None):
        """Add a new medication to the system"""
        med_id = f"med_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        medication = {
            "id": med_id,
            "name": name,
            "dosage": dosage,
            "time": time,  # Store exact scheduled time
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
        """Get medications based on filter type"""
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
        """Update an existing medication"""
        if med_id in self.medications:
            self.medications[med_id].update(updates)
            st.session_state.medications = self.medications
            self.save_medications()
            return self.medications[med_id]
        return None

    def delete_medication(self, med_id):
        """Delete a medication"""
        if med_id in self.medications:
            del self.medications[med_id]
            st.session_state.medications = self.medications
            self.save_medications()
            return True
        return False

    def save_medications(self):
        """Save medications to JSON file"""
        try:
            with open("medications.json", "w") as f:
                json.dump(self.medications, f, indent=2)
        except Exception as e:
            st.error(f"Error saving medications: {e}")

    def load_medications(self):
        """Load medications from JSON file"""
        try:
            if os.path.exists("medications.json"):
                with open("medications.json", "r") as f:
                    loaded_meds = json.load(f)
                    self.medications = loaded_meds
                    st.session_state.medications = loaded_meds
        except Exception as e:
            st.error(f"Error loading medications: {e}")

def send_notification(title, message):
    """Send a desktop notification"""
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
    """Background thread to check and send medication reminders"""
    while True:
        if st.session_state.notifications_enabled:
            ist = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist)
            current_minute = current_time.strftime("%H:%M")
            
            for med in st.session_state.medications.values():
                if med['status'] == 'pending' and med.get('reminder_settings', {}).get('enabled'):
                    scheduled_time = med['time']  # User selected time
                    
                    # Check main medication time
                    if current_minute == scheduled_time:
                        send_notification(
                            "Medication Reminder",
                            f"Time to take {med['name']} - {med['dosage']}"
                        )
                    
                    # Check advance reminder
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
        
        tm.sleep(30)  # Check every 30 seconds

# Start the notification checking thread
notification_thread = threading.Thread(target=check_medication_times, daemon=True)
notification_thread.start()

            help="Choose the time you want to take this medication"
