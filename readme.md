# ZaraiLink - Agri-Trade Intelligence Platform

## Progress Update 2: Features Implemented
- User Authentication (Signup, Login, Email Verification, Forgot Password)
- Trade Directory (Find Suppliers, Find Buyers)
- Supplier/Buyer Profile Pages (Overview, Key Contacts)
- Contact Unlocking with Tokens
- Subscription Plans

## Tech Stack
- **Backend:** Django, Django REST Framework
- **Frontend:** React.js
- **Database:** PostgreSQL (planned), SQLite (default for now)
- **Authentication:** JWT
- **Styling:** Tailwind CSS (or plain CSS if you haven't added Tailwind yet)

## Prerequisites
- [Git](https://git-scm.com/)
- [Node.js & npm](https://nodejs.org/) (LTS version recommended)
- [Python 3.x](https://www.python.org/downloads/) (3.8 or higher recommended)
- A code editor (e.g., [VS Code](https://code.visualstudio.com/))

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/umarkashif21/ZaraiLink.git
    cd ZaraiLink
    ```

2.  **Backend Setup (Django):**
    *   Navigate to the backend directory:
        ```bash
        cd backend
        ```
    *   (Optional but recommended) Create a Python virtual environment:
        ```bash
        # On Windows
        python -m venv venv
        # Activate the virtual environment
        venv\Scripts\activate
        ```
    *   Install Python dependencies:
        ```bash
        pip install -r requirements.txt
        ```
    *   Run database migrations (to set up the database structure):
        ```bash
        python manage.py migrate
        ```
    *   (Optional) Create a superuser account for the Django admin:
        ```bash
        python manage.py createsuperuser
        ```
    *   Start the Django development server:
        ```bash
        python manage.py runserver
        ```
        The backend API will be running on `http://127.0.0.1:8000/`. The Django admin panel will be available at `http://127.0.0.1:8000/admin/`.

3.  **Frontend Setup (React):**
    *   Open a *new* terminal/command prompt window.
    *   Navigate to the frontend directory (from the main project root):
        ```bash
        cd frontend # Or cd ../frontend if you are still in the backend directory from the previous steps
        ```
    *   Install Node.js dependencies:
        ```bash
        npm install
        ```
    *   Start the React development server:
        ```bash
        npm start
        ```
        The React frontend will open in your browser at `http://localhost:3000/`.

4.  **Running Both:**
    *   You need *two* terminal windows open: one running the Django backend (`python manage.py runserver`) and one running the React frontend (`npm start`).

## Team Members
- Umar Kashif - FYP Lead
- Fahad Nadeem - Supreme Leader
- Ibrahim Rana - Leader
- Salman Adnan - Tech Lead
