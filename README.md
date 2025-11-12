💼 About Django Recruit(Sir-Kaptain)

Django Recruit is a full-featured recruitment and internship management platform built with Python Django. It simplifies the hiring process by connecting students, recruiters, and administrators in one efficient system — from job posting and application to review and selection.

This project showcases practical use of Django’s powerful backend combined with modern tools for task automation, testing, and asynchronous processing, making it both scalable and production-ready.

🛠️ Tech Stack & Tools

Django – Core backend framework

Pytest – Automated testing

Celery – Asynchronous task scheduling

Flower – Celery task monitoring dashboard

Redis – Message broker for Celery

🚀 Key Features

User Authentication (Login, Register, Password Reset)

Email-based Account Verification & Notifications

Create, Edit, Delete, and View Job Adverts

Apply for Internships or Jobs

Track Job Applications and Recruitment Progress

Recruiters can Accept, Reject, or Schedule Interviews

Admin Dashboard for centralized management

⚙️ Getting Started

Clone the repository and create an environment file from .env.sample.

Create and activate a virtual environment:

python3 -m venv venv
source venv/bin/activate


Install dependencies:

pip install -r requirements.txt


Run migrations and start the development server:

python manage.py makemigrations
python manage.py migrate
python manage.py runserver

🧩 Background Services

Start Celery worker:

celery -A core worker --loglevel=info


Launch Flower dashboard for monitoring:

celery -A core flower --port=5555

🧪 Testing

Run tests with:

pytest -v -rA

🧠 Summary

Django Recruit demonstrates a complete recruitment workflow system — robust, scalable, and production-oriented — designed to manage candidates, jobs, and communication seamlessly while highlighting modern Django development best practices.
