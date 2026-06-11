import time
import random

from prometheus_client import start_http_server, Counter

# Metrik erstellen
upload_metric = Counter(
    'file_uploads_total',
    'Anzahl der Uploads',
    ['dateityp', 'status']
)

def process_upload():
    file_types = ['image/png', 'image/jpeg', 'video/mp4']
    file_type = random.choice(file_types)

    # 90% Erfolgsquote
    if random.random() > 0.1:
        status = 'success'
        print(f"[UPLOAD] {file_type} erfolgreich gespeichert.")
    else:
        status = 'error_file_too_large'
        print(f"[UPLOAD] FEHLER: {file_type} ist zu gross!")

    # Metrik erhöhen
    upload_metric.labels(
        dateityp=file_type,
        status=status
    ).inc()

if __name__ == '__main__':
    print("Starte Datei-Upload Simulation...")

    # Metrics Server starten
    start_http_server(8000)

    while True:
        process_upload()
        time.sleep(random.uniform(0.2, 1.5))