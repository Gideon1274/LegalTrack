# LegalTrack

**LegalTrack** is a Django-based case management system designed for Local Government Units (LGUs) in Cebu Province, Philippines. It streamlines the submission, tracking, and processing of legal cases between municipal LGUs and the Provincial Capitol's legal office.

---

## 📋 Table of Contents

- [About the Project](#about-the-project)
- [Key Features](#key-features)
- [User Roles](#user-roles)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## 🎯 About the Project

LegalTrack is a comprehensive case management platform that digitizes and automates the workflow of legal case submissions from LGUs to the Provincial Capitol. The system provides:

- **For LGU Administrators:** A guided wizard interface to submit legal cases with complete documentation
- **For Capitol Staff:** Role-based dashboards for receiving, examining, approving, numbering, and releasing cases
- **For Citizens:** A public portal to track case status using tracking numbers
- **For Super Admins:** Analytics dashboard, user management, and comprehensive audit logging

### Problem It Solves

Previously, LGUs had to submit physical documents to the Capitol, leading to:

- Lost or misplaced paperwork
- Difficulty tracking case status
- Slow processing times
- Limited transparency

LegalTrack digitizes this entire workflow, providing real-time tracking, automated notifications, and complete audit trails.

---

## ✨ Key Features

### Case Management

- **Guided Case Submission Wizard** - Step-by-step interface for LGU staff to submit cases
- **Document Checklist System** - Ensures all required documents are uploaded before submission
- **Automated Tracking Numbers** - Unique identifiers in format: `[MUNICIPALITY][YYMMDD][SEQUENCE]`
- **Status Workflow Management** - Cases move through: Draft → Submitted → Received → Assigned → Under Review → Approved → Numbered → Released
- **Document Version Control** - All uploaded documents are securely stored with metadata

### Role-Based Access Control

- **Seven Distinct Roles** - Each with specific permissions and dashboards
- **Two-Factor Authentication** - Email-based account activation for new users
- **Session Timeout Protection** - Automatic logout after inactivity
- **Force Password Change** - Admins can require users to change password on first login
- **Account Lockout** - After 5 failed login attempts (30-minute lockout)

### Public Portal

- **Case Status Tracking** - Search cases by tracking number without authentication
- **Public Timeline View** - See case progress and status updates
- **FAQ System** - Frequently asked questions for citizens
- **Support Feedback** - Submit inquiries and feedback to administrators

### Administrative Features

- **User Management** - Create and manage staff accounts across different roles
- **Analytics Dashboard** - Real-time metrics on case submissions, processing times, and workload distribution
- **Audit Logging** - Complete audit trail of all user actions and case modifications
- **Report Generation** - Export case data and analytics to CSV
- **Assignment Load Balancing** - View examiner workloads to distribute cases evenly

### Security Features

- **Comprehensive Audit Logs** - Track all CRUD operations, authentication events, and case transitions
- **Server-Side Validation** - All form inputs validated on backend
- **Custom Authentication Backends** - Support for Staff ID login and email aliases
- **Middleware Protection** - Session timeout and forced password change enforcement
- **Secure File Uploads** - Document uploads stored outside web root with access controls

---

## 👥 User Roles

| Role                 | Abbreviation        | Responsibilities                                                  |
| -------------------- | ------------------- | ----------------------------------------------------------------- |
| **Super Admin**      | `super_admin`       | System administration, user management, analytics, audit logs     |
| **LGU Admin**        | `lgu_admin`         | Submit cases on behalf of their municipality, track submissions   |
| **Capitol Receiver** | `capitol_receiving` | Receive incoming cases from LGUs, verify completeness             |
| **Capitol Examiner** | `capitol_examiner`  | Review case details, conduct legal examination, request revisions |
| **Capitol Approver** | `capitol_approver`  | Approve or return cases for corrections                           |
| **Capitol Numberer** | `capitol_numberer`  | Assign official case numbers to approved cases                    |
| **Capitol Releaser** | `capitol_releaser`  | Mark cases as released and ready for pickup/delivery              |

---

## 🛠 Tech Stack

### Backend

- **Django 5.2** - Web framework
- **Python 3.11+** - Programming language
- **Django REST Framework** - API endpoints (optional/future use)
- **Pillow** - Image processing for uploads

### Frontend

- **Django Templates** - Server-rendered HTML
- **React 18** (Optional) - Modern frontend in `frontend/` directory
- **Vite** - Build tool for React development
- **Tailwind CSS** - Utility-first CSS framework

### Database

- **SQLite** - Default for local development
- **PostgreSQL (Supabase)** - Production-ready option with cloud hosting

### Infrastructure

- **Vercel** - Deployment platform (configured via `vercel.json`)
- **Media Storage** - Local filesystem (`media/` directory)
- **Static Files** - Collected to `staticfiles/` for production

---

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Git** - Version control
- **Python 3.11 or higher** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** (optional) - Only needed for React frontend development
- **PowerShell** (Windows) or Terminal (macOS/Linux)

---

## 🚀 Installation

### 1. Clone the Repository

```powershell
git clone https://github.com/Gideon1274/LegalTrack.git
cd LegalTrack
```

### 2. Create and Activate Virtual Environment

**Windows (PowerShell):**

```powershell
py -m venv legaltrack_env
.\legaltrack_env\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python3 -m venv legaltrack_env
source legaltrack_env/bin/activate
```

### 3. Install Python Dependencies

```powershell
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

**For development with additional tools:**

```powershell
py -m pip install -r requirements-dev.txt
```

---

## ⚙️ Configuration

### 1. Create Environment File

Copy the example environment file:

```powershell
Copy-Item env.example .env
```

### 2. Configure Environment Variables

Edit `.env` and set the following variables:

#### Required Settings

```env
# Security
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# Database Provider (choose one)
LEGALTRACK_DB_PROVIDER=sqlite
```

#### Database Options

**Option A: SQLite (Recommended for Development)**

```env
LEGALTRACK_DB_PROVIDER=sqlite
```

- No additional configuration needed
- Database file: `db.sqlite3`
- Best for: Local development and testing

**Option B: PostgreSQL via Supabase (Recommended for Production)**

```env
LEGALTRACK_DB_PROVIDER=supabase
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME
```

- Replace `USER`, `PASSWORD`, `HOST`, and `DBNAME` with your Supabase credentials
- Get connection string from [Supabase Dashboard](https://supabase.com)
- Optional fallback: `LEGALTRACK_ALLOW_SQLITE_FALLBACK=true`

#### Optional Settings

```env
# Email (for production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password

# Session timeout (in seconds, default 1800 = 30 minutes)
SESSION_TIMEOUT=1800
```

### 3. Run Database Migrations

```powershell
py manage.py migrate
```

This creates all necessary database tables for:

- Users and authentication
- Cases and documents
- Audit logs
- FAQ and support feedback

### 4. Create a Superuser Account

```powershell
py manage.py createsuperuser
```

Follow the prompts to create your Super Admin account. You'll need:

- Email address
- Password (minimum 8 characters)

---

## 🏃 Running the Application

### Start the Django Development Server

```powershell
py manage.py runserver
```

The application will be available at:

- **Main Application:** http://127.0.0.1:8000/
- **Admin Panel:** http://127.0.0.1:8000/admin/
- **Login Page:** http://127.0.0.1:8000/accounts/login/
- **Public Tracking:** http://127.0.0.1:8000/track/
- **Support Portal:** http://127.0.0.1:8000/support/

### Access the Application

1. **Log in as Super Admin:**
   - Navigate to http://127.0.0.1:8000/accounts/login/
   - Use the superuser credentials you created
   - You'll be directed to the Super Admin dashboard

2. **Create Additional Users:**
   - From Super Admin dashboard, go to "Manage Users"
   - Create accounts for LGU Admins, Capitol Staff, etc.
   - Each user receives an activation email (check console in development)

3. **Test Case Submission:**
   - Log in as an LGU Admin
   - Navigate to "Submit New Case"
   - Follow the wizard to submit a test case

---

## 🎨 Frontend Setup (Optional)

If you want to work on the React frontend located in `frontend/`:

### 1. Install Node.js Dependencies

```powershell
cd frontend
npm install
```

### 2. Start the React Development Server

```powershell
npm run dev
```

The React app will run on http://127.0.0.1:5173 and automatically proxy API requests to Django at http://127.0.0.1:8000.

**Note:** The React frontend is optional. The Django application is fully functional with server-rendered templates.

---

## 🧪 Testing

### Run All Tests

```powershell
py manage.py test
```

### Run Tests for Specific App

```powershell
py manage.py test core
```

### Run Tests with Coverage (if installed)

```powershell
coverage run --source='.' manage.py test
coverage report
coverage html
```

View coverage report by opening `htmlcov/index.html` in a browser.

---

## 📁 Project Structure

```
LegalTrack/
├── core/                       # Main application
│   ├── models.py              # Database models (User, Case, AuditLog, etc.)
│   ├── views.py               # View logic for all pages
│   ├── auth_views.py          # Authentication views
│   ├── forms.py               # Django forms
│   ├── backends.py            # Custom authentication backends
│   ├── middleware.py          # Session timeout, force password change
│   ├── signals.py             # Django signals (audit logging)
│   ├── urls.py                # URL routing
│   ├── templates/             # HTML templates
│   │   ├── base.html          # Base template
│   │   ├── core/              # App-specific templates
│   │   └── registration/      # Auth templates
│   └── migrations/            # Database migrations
│
├── legaltrack/                # Project settings
│   ├── settings.py            # Django configuration
│   ├── urls.py                # Root URL configuration
│   └── wsgi.py                # WSGI application
│
├── frontend/                  # React frontend (optional)
│   ├── src/                   # React source code
│   ├── package.json           # Node dependencies
│   └── vite.config.js         # Vite configuration
│
├── media/                     # User-uploaded files
│   └── cases/                 # Case documents organized by tracking ID
│
├── static/                    # Static files (CSS, JS, images)
├── staticfiles/               # Collected static files for production
│
├── scripts/                   # Utility scripts
│   └── create_case_supabase.py
│
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
├── requirements-dev.txt       # Development dependencies
├── vercel.json                # Vercel deployment config
├── env.example                # Example environment variables
└── README.md                  # This file
```

---

## 🔧 Troubleshooting

### PowerShell Script Execution Error

If you get an error activating the virtual environment:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then try activating again.

### Database Changes Not Reflected

After modifying models, run:

```powershell
py manage.py makemigrations
py manage.py migrate
```

### Static Files Not Loading

Collect static files:

```powershell
py manage.py collectstatic
```

### Port Already in Use

If port 8000 is already in use, specify a different port:

```powershell
py manage.py runserver 8080
```

### Email Activation Not Working

In development, activation emails are printed to the console. Check your terminal output for the activation link.

For production, configure SMTP settings in `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Supabase Connection Issues

If you can't connect to Supabase:

1. Verify your `DATABASE_URL` is correct
2. Check that your IP address is allowed in Supabase project settings
3. Enable SQLite fallback: `LEGALTRACK_ALLOW_SQLITE_FALLBACK=true`

### Media Files Not Accessible

Ensure `MEDIA_ROOT` and `MEDIA_URL` are configured in `settings.py` and that the Django development server is serving media files.

---

## 📄 License

This project is part of a university capstone project. All rights reserved.

---

## 👨‍💻 Contributing

This is a capstone project. For questions or issues, please contact the project maintainer.

---

## 📞 Support

For technical support or questions about deployment:

- Check the [SDD_LegalTrack.md](SDD_LegalTrack.md) for detailed system documentation
- Review Django logs in the console
- Check the Admin panel audit logs for system events

---

**Built with ❤️ for the Province of Cebu**
