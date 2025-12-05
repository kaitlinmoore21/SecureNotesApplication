Insecure version running information: 

# Activate the virtual 
python -m venv .venv

# Run Virtual Environment:
.\venv\Scripts\activate

# Install Dependencies: Install all necessary packages (FastAPI, Uvicorn, SQLAlchemy, etc.):
pip install -r requirements.txt

# Start the Server:
python run.py

# Access the Application: 
http://127.0.0.1:8002/insecure/register


--------------------------------------------------------------------------------------------------------------------------


Secure version running information: 

# Activate the virtual 
python -m venv .venv 

# Run the enviroment
.\venv\Scripts\Activate

# Install required libraries
pip install fastapi uvicorn[standard] python-dotenv sqlalchemy python-multipart passlib[bcrypt] jinja2

# Start the server: 
python -m uvicorn app.secure.main:app --reload

# Access the Application:
http://127.0.0.1:8000/secure/register