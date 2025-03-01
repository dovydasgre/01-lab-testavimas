FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install pymongo Flask Flask-PyMongo

CMD ["python", "app.py"]
