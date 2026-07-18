# 📧 Email Notification Portal

The Email Notification Portal is the first workflow module of **OpsFlow**, designed to streamline communication between the Application Support/SRE team and partner financial institutions during production incidents.

It enables engineers to quickly generate and send standardized email notifications, reducing manual effort and ensuring consistency during incident response.

## Features

- Select an institution from a configured list
- Filter notifications by transaction response code
- Add optional investigation comments
- Automatically retrieve recent sample transactions
- Generate an Excel attachment containing sample transactions
- Preview the complete email before sending
- Preview attachment details, including:
  - Attachment filename
  - Number of sample transactions
  - Latest transaction timestamp
- Send emails via SMTP with configurable To and CC recipients

## Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- MySQL
- OpenPyXL
- SMTP

### Frontend
- React
- Vite
- Tailwind CSS
- shadcn/ui
- Radix UI
- Axios

## Workflow

1. Select the target institution.
2. Optionally select a response code.
3. Add additional comments if required.
4. Choose whether to attach sample transactions.
5. Preview the email and attachment metadata.
6. Confirm and send the notification.

## Purpose

This module reduces manual effort during production incidents by ensuring notifications are consistent, accurate, and backed by recent transaction data.



<img width="534" height="445" alt="image" src="https://github.com/user-attachments/assets/4edffb18-c8a5-4ce5-a726-14f2e6b860c6" />
