# PTPay - Public Transportation Payments System

A backend system built with Django and Django REST Framework to simulate NFC-based payments for public transportation.  
The system allows drivers and passengers to interact through smart cards, with real-time payment processing and trip tracking.

## 🔧 Features

- 🚍 Register and manage drivers & passengers
- 💳 Simulate NFC card payments via API
- 📍 Track trips and payment history
- 🔒 Token-based authentication
- 📤 Project deployed and backed up using PythonAnywhere

## 📦 Technologies Used

- Python 3.10
- Django 5.x
- Django REST Framework
- SQLite (development)
- NFC Simulation
- Git + GitHub
- PythonAnywhere for deployment

## 📂 How to Run the Project Locally

```bash
git clone https://github.com/mousa8080/PTPay-Public-Transportation-Payments-system.git
cd PTPay-Public-Transportation-Payments-system
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
