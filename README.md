# Inventory Management API

This is a professional FastAPI application built for Week 4 of the Python pathway. It demonstrates advanced API concepts including relational database management, custom authentication middleware, rate limiting, and asynchronous background tasks.

## Technical Specifications

- **Database:** SQLite (Relational storage for items and authentication keys).
- **Security:** Header-based API Key authentication.
- **Traffic Control:** Rate limiting via `slowapi` to prevent service abuse.
- **Concurrency:** Asynchronous background tasks for non-blocking audit logging.

## Installation and Execution

To install the package directly from TestPyPi:

```bash
pip install --index-url [https://test.pypi.org/simple/](https://test.pypi.org/simple/) resolution_week4_YOUR_USERNAME