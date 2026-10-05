FROM python:3.12.15-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg
WORKDIR /workspace
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY scripts ./scripts
COPY data ./data
COPY docs ./docs
COPY playground.ipynb ./playground.ipynb
CMD ["python", "scripts/execute_notebook.py"]
