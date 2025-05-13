FROM python:3.12.9
WORKDIR /demoapp
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8520
COPY . /demoapp
CMD ["streamlit", "run", "Home.py", "--server.port=8520", "--server.address=0.0.0.0"]