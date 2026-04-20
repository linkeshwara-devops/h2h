FROM python:3.10

WORKDIR /app

COPY . .   # VERY IMPORTANT (copies templates + static)

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]
