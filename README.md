# Bloom Server

FastAPI server for the Bloom application.

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # for Linux/Mac
# or
.\venv\Scripts\activate  # for Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

Start the server using the command:
```bash
uvicorn main:app --reload
```

The server will be available at: http://localhost:8000

## API Documentation

After starting the server, the API documentation is available at the following addresses:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc