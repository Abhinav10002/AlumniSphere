# 🎓 AlumniSphere

**AlumniSphere** is a modern, full-stack web application designed to bridge the gap between college alumni, current students, and university administration. It provides a centralized platform for networking, sharing community updates, and fostering professional relationships.

🚀 **Live Application:** [https://alumnisphere-pfxd.onrender.com](https://alumnisphere-pfxd.onrender.com)

---

## ✨ Features

* **🔐 Secure Authentication:** User registration/login with email verification (OTP via Gmail SMTP).
* **👤 Alumni Profiles:** Rich user profiles featuring academic history, career progression, and contact details.
* **📰 Community Feed:** Interactive post sharing with support for media file uploads.
* **☁️ Stateless Cloud Media Management:** Dynamic media and document storage powered by Cloudinary.
* **⚡ Production-Grade Database:** Relational database management using Aiven Cloud MySQL over secure SSL.
* **📱 Responsive UI:** Mobile-friendly design optimized for desktops, tablets, and mobile devices.

---

## 🛠️ Tech Stack

### **Backend & Framework**
* **Language:** Python 3.10+
* **Framework:** Django 4.2+
* **WSGI Server:** Gunicorn

### **Database & Media**
* **Database:** Aiven Managed MySQL (connected via `PyMySQL` & SSL)
* **Media Storage:** Cloudinary
* **Static File Handling:** WhiteNoise

### **Deployment & Infrastructure**
* **Hosting Platform:** Render
* **CI/CD Pipeline:** Automated build scripts (`build.sh`) connected to GitHub
* **Authentication/Email:** Gmail SMTP Service

---

## 🏗️ Architecture Overview

```text
[ Client Browser ]
        │
        ▼
[ Render Web Service (Gunicorn / Django) ]
        │
        ├──────────────────────────┐
        ▼                          ▼
[ Aiven Managed MySQL ]   [ Cloudinary Media ]
 (SSL Encrypted DB)       (Avatars & Attachments)
