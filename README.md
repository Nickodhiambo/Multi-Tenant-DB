## An App Implementing a Multi-tenant Database Architecture
### Overview
This is an app with a multi-tenant database architecture implemented using Python's
FastAPI framework. The app consists of a core database that manages organizations, also
called tenants, data. When a core user creates an organization, the app automatically creates
a tenant database. Each tenant has their own database, ensuring complete isolation of tenant data.
Users can authenticate at either the core level or the tenant level

### Features
* A multi database architecture comprising one core database and several tenant databases
* Authentication at both core and tenant levels
* Organization creation by authenticated core users
* Automatic provision of tenant database upon organization creation
* A single authentication interface for both core and tenant users
* Interfaces to view and manipulate tenant user information
* A robust security system implemented using JWT and bcrypt

### Setup Instructions
#### Prerequisites
* Python 3.8+
* PostgreSQL database version 10+. Check [this](https://www.prisma.io/dataguide/postgresql/setting-up-a-local-postgresql-database) guideline for more info on how to set up the database locally
* A running postgreSQL database instance

#### Installation
1. Clone the git repository into a local folder
```bash
git clone https://github.com/Nickodhiambo/Multi-Tenant-DB.git
```

2. Create a virtual environment and activate it
```bash
python -m venv venv
source venv/bin/activate # venv\Scripts\activate on Windows
```

3. Install project dependencies using pip
```bash
pip install -r requirements.txt
```

4. Create a .env file in the root directory with the following information
```
database_url = "postgresql+asyncpg://<username>:<password>@localhost:5432/<database name>"
jwt_secret_key = ""
jwt_algorithm = "HS256"
jwt_access_token_expire_minutes = 30
```
Replace <username> with your postgreSQL username, <password> with your postres password and
<database name> with the name you chose for your running database instance

5. Apply database migrations
```bash
alembic upgrade head
```

6. Start your local application server
```bash
uvicorn app.main:app --reload
```

### Usage
With your server up and running, visit http://127.0.0.1:8000/docs#/ to authenticate as a 
core user. As an authenticated core user, you can create organizations, view and update user
profile from the browser.

Create a core user account by passing an email, password and full name to the `Register` endpoint.
To create an organization and view user profiles, log in using the `Login` endpoint and copy the generated access token from the request body.You need to authorize to be able to create organizations and view user profiles. To authorize, click on the `Authorize` button on the top right corner and paste the JWT token in the input field provided.

The API testing GUI that ships with FastAPI is limited. You cannot pass a header into a request,
only the request body. The API endpoints for registering and logging in a tenant user require one to pass a 'X-TENANT' header whose value will be the name of the database that stores the tenant's info. For this, you will need to use a versatile GUI like Postman.

In Postman, click on the headers parameter and insert the 'X-TENANT' header and the name of a database (could be anything) as its value when registering a tenant user. A tenant database with the name you passed in the header will be created if it does not already exist, or updated with the value of the authenticating tenant if it exists. Pass the same 'X-TENANT' header when logging in with the same tenant user.

### Testing
Testing covers the core functionality of the API:
* Core and tenant user authentication
* User management
* Organization creation

To test these functionality, run from the root directory:
```python
pytest -v -s test
```

### API Documentation
Visit http://127.0.0.1:8000/docs#/ to read API documentation