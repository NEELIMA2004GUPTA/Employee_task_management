**EMPLOYEE TASK MANAGEMENT**
A Django REST Framework (DRF) based Task Management API that provides secure CRUD operations for tasks, password reset functionality using email, and bulk task uploads via Excel files.

FEATURES:
1) User Authentication (JWT / Session-based depending on configuration)
2) CRUD Operations on tasks (Create, Read, Update, Delete)
3) Forgot & Reset Password functionality using uid and token
4) Excel File Upload to bulk-create tasks
5) Validation, error handling, and skipped-row reporting during Excel upload

Tech Stack:
Backend: Django, Django REST Framework
Database: MySQL
Authentication: Django’s built-in auth system
Email: Django’s send_mail utility (SMTP-based)
Excel Handling: OpenPyXL

Steps to run this project in remote system:
1) Clone the repository
2) Create and activate a virtual environment 
        For creating virtual environment- python-m venv <virtual_env_name>
        For activating the virtual environment- <virtual_env_name>\Scripts\activate
3) Install dependencies
        pip install -r requirements.txt
4) Start the server
        cd employee_task
        python manage.py runserver
   
API Endpoints
**FOR CRUD OPERATION**
Method        Endpoint                      Description
GET	          /api/tasks/	          Get all tasks for the logged-in user
POST	        /api/tasks/	          Create a new task (assigned to logged-in user)
GET	          /api/tasks/{id}/	    Get task details by ID
PUT	          /api/tasks/{id}/	    Update entire task
PATCH	        /api/tasks/{id}/	    Partially update a task
DELETE	      /api/tasks/{id}/	    Delete a task


**Authentication & Password Reset**
Method	        Endpoint	                    Description
POST	          /api/forgot-password/	      Request password reset email
POST	          /api/reset-password/	      Reset password using uid and token

**Excel Upload**
Method	        Endpoint	                        Description
POST	          /api/upload-tasks-excel/	   Upload an Excel file to create tasks in bulk


Error Handling

Database Errors → 500 Internal Server Error with details
Validation Errors → 400 Bad Request with field-specific messages
Not Found → 404 Task not found
Skipped Rows in Excel Upload → Returned with reasons (missing title, invalid user, invalid date, duplicate task, etc.)

Happy Coding!
