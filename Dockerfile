FROM python:3.10.12
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY . /app
EXPOSE 8080
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt
CMD ["python", "app.py"]