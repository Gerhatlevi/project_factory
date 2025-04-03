# Python alap image használata
FROM python:3.12-slim

# Munkakönyvtár beállítása
WORKDIR /app

# Függőségek másolása és telepítése
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-setuptools \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools

# Alkalmazás másolása
COPY . .

# Port megnyitása
EXPOSE 8080

# Alkalmazás indítása
CMD ["streamlit", "run", "main.py", "--server.port=8080", "--server.address=0.0.0.0"]