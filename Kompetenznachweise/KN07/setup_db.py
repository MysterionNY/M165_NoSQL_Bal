import chromadb

client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_or_create_collection(name="resumes")

documents = [
    "Experte im Erstellen von responsiven Benutzeroberflächen mit React und CSS.",
    "Langjährige Erfahrung in der Konfiguration von AWS-Servern und Docker-Containern.",
    "Spezialisiert auf Datenanalyse, Machine Learning und das Trainieren von Modellen in Python.",
    "Führungskraft mit Fokus auf agile Methoden, Scrum und Team-Coaching."
]

ids = ["cv_1", "cv_2", "cv_3", "cv_4"]

collection.add(documents=documents, ids=ids)

print("Lebensläufe wurden erfolgreich vektorisiert und gespeichert!")