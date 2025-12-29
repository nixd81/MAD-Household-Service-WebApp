# 🏠 Household Services Application  
### Modern Application Development I (MAD I) – Sept 2024

**Student Name:** Nirmit Desai  
**Roll Number:** 23F3001502  
**Course:** Modern Application Development I  
**Institute:** IIT Madras (Online Degree Program)

---

## 📌 Project Overview

The **Household Services Application** is a multi-user web platform designed to connect **customers** with **service professionals** for common household services such as plumbing, AC servicing, electrical work, etc.

The application supports **three roles**:
- **Admin**
- **Service Professional**
- **Customer**

It is built using **Flask**, **Jinja2 + Bootstrap**, and **SQLite**, and is fully runnable on a **local machine** as required by the course.

---

## 🎯 Problem Statement

Design and implement a platform that:
- Allows customers to book household services
- Enables service professionals to manage service requests
- Provides administrators with full control to monitor users, services, and platform activity

---

## 🧑‍💼 User Roles & Responsibilities

### 🔑 Admin (Superuser)

- Login redirects to Admin Dashboard
- Manage all users (customers and service professionals)
- Create, update, and delete services
- Approve service professionals after document verification
- Block/unblock users based on fraud or poor reviews
- Search users and services
- View platform statistics

> Admin does **not** require registration

---

### 🧑‍🔧 Service Professional

- Register and login
- Each professional provides **only one service type**
- View assigned service requests
- Accept or reject service requests
- Close a service request after completion
- Profile visibility depends on customer ratings and reviews
- Exit service location once service is closed by customer

---

### 🧑‍💻 Customer

- Register and login
- View and search available services by:
  - Service name
  - Location / pin code
- Create service requests
- Edit or close service requests
- Post reviews and remarks after service completion

---

## 🛠 Core Functionalities

### 1️⃣ Authentication
- Separate login/register for:
  - Customer
  - Service Professional
  - Admin
- User roles stored and handled at the model level

---

### 2️⃣ Admin Dashboard
- Manage users and services
- Approve professionals
- Block/unblock users
- Monitor service requests and ratings

---

### 3️⃣ Service Management (Admin)
- Create new services with base price and duration
- Update service details
- Delete existing services

---

### 4️⃣ Service Requests (Customer)
- Create new service requests
- Edit request details
- Close service requests after completion

---

### 5️⃣ Search
- Customers can search services by name or location
- Admin can search customers and professionals

---

### 6️⃣ Service Request Actions (Professional)
- View all service requests
- Accept or reject requests
- Close requests after completion

---

## 🧱 Tech Stack

- **Backend:** Flask
- **Frontend:** Jinja2 Templates + Bootstrap
- **Database:** SQLite (via SQLAlchemy)
- **Authentication:** Flask-Login
- **Security:** Werkzeug (password hashing)
- **Utilities:** datetime, pytz, os

---

## 🗃 Database Design

### Tables

- **Admin**
- **Customer**
- **ServiceProfessional**
- **Service**
- **ServiceRequest**
- **AcceptedRequest**
- **Rating**

### Key Relationships

- Customer ↔ ServiceRequest ↔ ServiceProfessional
- Service ↔ ServiceRequest
- ServiceRequest ↔ Rating

---

## 🌐 API / Route Endpoints

### General
- `/` – Home page

### Authentication
- `/login/customer`
- `/register/customer`
- `/login/professional`
- `/register/professional`
- `/login/admin`
- `/logout/customer`
- `/logout/professional`
- `/logout/admin`

### Customer
- `/customer_homepage`
- `/services/<service_name>`
- `/edit_profile`
- `/customer_summary/<customer_id>`
- `/rate/<service_id>`
- `/chat_with_professional`

### Professional
- `/professional_homepage`
- `/service_request/<request_id>/action`
- `/edit_profile_professional`
- `/accepted_service/<service_id>`
- `/chat_with_customer`

### Admin
- `/admin_homepage`
- `/add_service`
- `/delete_professional/<prof_id>`
- `/view_customers`
- `/view_professional`
- `/view_services`
- `/view_service_requests`
- `/view_accepted_services`
- `/view_ratings`
- `/search/admin`

---

## 📽 Project Demo Video

Google Drive Link (public access):  
https://drive.google.com/file/d/14CQxchq0PwbkUSi0k-YJMnnHM3IwTUo8/view
