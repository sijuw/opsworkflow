# OpsFlow

> A modular SRE Workflow Automation Platform designed to eliminate operational toil, standardize support processes, and improve incident response efficiency.

---

## 📖 Overview

OpsFlow is a full-stack internal engineering platform built to automate repetitive operational tasks performed by Application Support and Site Reliability Engineering (SRE) teams.

Rather than relying on manual procedures, OpsFlow provides reusable workflows that standardize operational activities, reduce response time, improve consistency, and enhance engineer productivity.

The platform is built with a modular architecture, allowing new workflows to be added without impacting existing functionality.

---

## ✨ Current Features (v1.0)

### 📧 Email Notification Workflow

Automates partner communication during production incidents by:

- Selecting a financial institution
- Selecting a response code
- Adding optional operational context
- Retrieving recent failed transactions from the transaction database
- Generating a formatted Excel attachment
- Previewing the exact email before sending
- Sending notifications via SMTP

### Email Preview

Before dispatching, engineers can verify:

- Subject
- Recipients (To & CC)
- Email body
- Attachment filename
- Number of sample transactions
- Latest transaction timestamp

This helps eliminate incorrect notifications and improves confidence before sending.

### Excel Report Generation

Automatically generates an Excel report containing transaction samples including:

---

## 🏗 Planned Workflows

OpsFlow has been designed as a modular platform.

Upcoming workflows include:

- Enable Service Logging
- Switch Bank VPN Connections
- Refresh Interchange
- Institution Management
- Operational Reporting
- Incident Timeline
- RCA Assistant
- Additional SRE automation workflows

---

## 🛠 Technology Stack

### Frontend

- React
- Vite
- React Router
- Tailwind CSS
- shadcn/ui
- Lucide Icons

### Backend

- FastAPI
- SQLAlchemy
- Pydantic
- SMTP
- OpenPyXL

### Database

- SQLite (Configuration)
- MySQL (Transaction Data)

### Infrastructure

- Docker *(Planned)*
- Kubernetes *(Deployment Target)*

---

## 📁 Project Structure

```
opsflow/
│
├── backend/
│
├── frontend/
│
├── docs/
│
└── k8s/ (Coming Soon)
```

---

## 🚀 Roadmap

### v1.0

- Dashboard
- Email Notification Workflow
- Email Preview
- Excel Generation
- SMTP Integration

### v1.1

- Enable Logging Workflow

### v1.2

- Switch Institutions VPN Workflow

### v1.3

- Refresh Interchange Workflow

### v1.4

- Institution Management

### v2.0

- Authentication
- RBAC
- Audit Logs
- Workflow History
- Metrics Dashboard

---

## 🎯 Project Goals

OpsFlow aims to:

- Reduce operational toil
- Standardize repetitive support tasks
- Improve incident response efficiency
- Minimize human error
- Increase workflow consistency
- Enable self-service operational automation

---

## 📸 Screenshots

### Dashboard

> <img width="760" height="783" alt="image" src="https://github.com/user-attachments/assets/3552bdda-9d82-4598-8953-9f8a36770069" />


### Email Notification Workflow

> <img width="433" height="422" alt="image" src="https://github.com/user-attachments/assets/1eaca211-f106-4c03-a51d-2fbb70cf7406" />


### Email Preview

> <img width="443" height="524" alt="image" src="https://github.com/user-attachments/assets/ede2a7e9-7894-4eb1-8439-3d2b01a3ec3c" />


---

## 👨‍💻 Author

**Saheed Yusuf**

Senior Application Support Engineer

LinkedIn:
https://linkedin.com/in/saheed-yusuf
