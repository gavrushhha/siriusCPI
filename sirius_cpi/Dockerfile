FROM python:3.11-slim

WORKDIR /sirius_cpi

COPY requirements.txt /sirius_cpi/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /sirius_cpi

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
