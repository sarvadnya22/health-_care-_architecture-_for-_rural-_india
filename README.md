# HealthGuard Telemedicine System

HealthGuard is a comprehensive telemedicine and rural healthcare monitoring system designed to connect Patients, ASHA Workers, Doctors, and Pharmacies. It leverages AI agents for triage, vital monitoring, and automated workflow management.

## 🚀 Features

-   **Multi-Role Dashboard**: Specialized interfaces for Patients, Doctors, ASHA Workers, and Pharmacists.
-   **AI-Powered Triage**: Automated symptom analysis and risk assessment using Machine Learning.
-   **Agent System**:
    -   **Triage Agent**: Analyzes symptoms and suggests home remedies or doctor referrals.
    -   **Vital Trend Analyzer**: Monitors blood pressure and other vitals for alarming trends.
    -   **Orchestrator**: Manages daily analysis and workflow automation.
-   **Pharmacy Management**: Inventory tracking and prescription dispensing.
-   **Appointment & Referral System**: Seamless referral flow from ASHA workers to Doctors.

## 🛠️ Tech Stack

-   **Backend**: Python (Flask)
-   **Database**: SQLite
-   **AI/ML**: Scikit-learn, Pandas, Hugging Face Datasets
-   **Frontend**: HTML, CSS, JavaScript (Bootstrap/Custom)

## ⚙️ Installation & Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Initialize Database**:
    This script sets up the database schema, including agent tables and sample data.
    ```bash
    python setup_database.py
    ```
    *(Note: This resets the `health.db` file)*

3.  **Train ML Model**:
    Required for the AI Triage system to function.
    ```bash
    python train_model_remedies.py
    ```
4.  **Seed Demo Data**:(⚙️  OPTIONAL ) single time command to create demo data
    ```bash
    python seed_demo_data.py
    ```

5.  **Run the Application**:
    ```bash
    python app.py
    ```
    Access the app at: `http://127.0.0.1:5000`

## 🔐 Login Credentials (Demo)

| Role | Login URL | Username / Phone | Password |
| :--- | :--- | :--- | :--- |
| **Patient** | `/login` | `+919876543210` | `password123` |
| **ASHA Worker** | `/worker_login` | `+919834358534` | `asha123` |
| **Doctor** | `/doctor/login` | `doctor@hospital.gov` | `doctor123` |
| **Pharmacist** | `/pharmacy/login` | `pharma@health.com` | `pharma123` |
| **Health Ministry** | `/health_dept/login` | `minister@health.gov` | `admin123` |

## 🧪 Testing

-   **AI Triage**: Log in as an ASHA worker, select a patient, and use "Add Report" to test the AI symptom analysis.
-   **SOS Alert**: Trigger an SOS from the ASHA dashboard to see the emergency workflow in action.
-   **Prescriptions**: Doctors can prescribe meds, which appear instantly in the Pharmacy dashboard for dispensing.
