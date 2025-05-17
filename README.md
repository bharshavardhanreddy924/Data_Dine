# 🍽️ Data_Dine

A full-stack restaurant management web application built using Flask and MongoDB that supports both **Admin** and **Customer** functionalities. It allows users to register, browse the menu, place orders, and view order history, while administrators can manage menu items and view customer orders through a secure admin dashboard.

---

## 🚀 Live Demo
- 🟢 **Render**: [https://data-dine.onrender.com](https://data-dine.onrender.com)

---

## 🔐 Access Credentials

### Admin Login
- **Username:** `admin`
- **Password:** `admin123`

### User Login
- Register directly from the application homepage

---

## 📦 Features

### 🧑‍💼 Admin Panel
- Secure admin login
- Dashboard view for analytics
- Add, update, and delete menu items
- View all customer orders

### 🧑‍🍳 Customer Interface
- User registration and login
- Browse available menu items
- Add to cart and place orders
- View past order history

---

## 🧰 Tech Stack

| Layer        | Technology          |
|--------------|---------------------|
| Frontend     | HTML, CSS   |
| Backend      | Python (Flask)      |
| Database     | MongoDB (using `pymongo`) |
| Deployment   | Render, Vercel      |
| Auth System  | Session-based login |

---

## 📁 Folder Structure

```
Data_Dine/
├── static/                 # Static files (CSS, images)
├── templates/              # HTML templates using Jinja2
│   ├── admin.html
│   ├── cart.html
│   ├── dashboard.html
│   ├── index.html
│   ├── login.html
│   ├── menu.html
│   └── register.html
├── app.py                  # Main Flask application
├── requirements.txt        # Required Python dependencies
├── vercel.json             # Vercel deployment config
├── build.sh                # Render deployment build script
├── wsgi.py                 # WSGI entry point
└── README.md               # This file
```

---

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- `pip` package manager
- MongoDB Atlas or local MongoDB setup

### Step-by-Step Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/bharshavardhanreddy924/Data_Dine.git
   cd Data_Dine
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Create a `.env` file (manually or using export) and add:
   ```env
   MONGO_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/datadine
   SECRET_KEY=your_secret_key
   ```

5. **Run the development server**
   ```bash
   python app.py
   ```

6. Open your browser at:  
   [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🧪 Usage Guide

### Admin Dashboard
- Log in using credentials (`admin` / `admin123`)
- View all customer orders
- Add new menu items with name, price, and description
- Delete outdated dishes

### Customer Flow
1. Register using a unique email
2. Login with registered credentials
3. Browse the menu and add items to cart
4. Checkout to place an order
5. View order history from profile/dashboard

---

## 🔌 Deployment Guide

### Render Deployment

- Uses `build.sh` and `wsgi.py`
- Add the following environment variables in Render dashboard:
  - `MONGO_URI`
  - `SECRET_KEY`

### Vercel Deployment

- Used for frontend fallback/static view
- Refer to `vercel.json` for config

---

CHECK THE REPORT - IT IS MORE DETAILED :)


## 🤝 Contributing

We welcome contributions! Here's how:

```bash
1. Fork the repo
2. Create a new branch: git checkout -b feature/awesome-feature
3. Commit your changes: git commit -m "Added awesome feature"
4. Push to the branch: git push origin feature/awesome-feature
5. Submit a Pull Request
```


## 📬 Contact

**Author**: B. Harshavardhan Reddy  
- 📧 [LinkedIn](https://in.linkedin.com/in/b-harshavardhan-reddy-08911b174)  
- 🌐 [GitHub Repo](https://github.com/bharshavardhanreddy924/Data_Dine)

---

> 🔔 *Note: This is a college-level demonstration project. Security, error handling, and production readiness should be enhanced before deploying to a real-world use case.
Contact me if u want this for real-world use case (I have improved version)*
