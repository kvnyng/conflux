# Server
Herein lies the code for the server. Data storage is through files (upload folders). All necessary files should automatically be created when ran.

## Running The Server
```uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug```