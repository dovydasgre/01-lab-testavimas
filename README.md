# 01-lab-testavimas

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)  
- [Docker Compose](https://docs.docker.com/compose/install/)  
- [Python 3](https://www.python.org/downloads/)

## Installation & Running the Project

1. **Clone the Repository**

   Open your terminal and run:

   ```bash
   git clone https://github.com/dovydasgre/01-lab-testavimas.git
   cd 01-lab-testavimas

2. **Start database and run tests**

   In your terminal and run:

   ```bash
   docker-compose up --build
   python test_api.py
