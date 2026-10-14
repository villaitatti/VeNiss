FROM python:3.12-alpine
COPY listener.py /app/listener.py
USER 1000:1000
ENV PYTHONUNBUFFERED=1
EXPOSE 9000
CMD ["python", "/app/listener.py"]
