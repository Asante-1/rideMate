FROM python:3.11-slim

COPY . .

RUN pip install -r ./core/requirements.txt
RUN python ./core/manage.py makemigrations
RUN python ./core/manage.py migrate

EXPOSE 9000

CMD ["python", "./core/manage.py", "runserver", "0.0.0.0:8000"]