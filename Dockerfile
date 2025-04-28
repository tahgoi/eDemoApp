FROM python:3.12
WORKDIR /webapp
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8510
COPY . /webapp
CMD ["streamlit", "run", "Home.py", "--server.port=8510", "--server.address=0.0.0.0"]