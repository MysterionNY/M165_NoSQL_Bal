import chromadb

client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_collection(name="resumes")

suchanfrage = "Frontend-Entwickler fürs Webdesign"

print(f"Suche nach Lebensläufen für: '{suchanfrage}'...")

# KORREKT: Semantische Suche über Vektor-Ähnlichkeit
resultate = collection.query(
    query_texts=[suchanfrage],
    n_results=2,
    include=["documents", "distances"]
)

print("\nPassende Lebensläufe:")

for index, document in enumerate(resultate["documents"][0]):
    distance = resultate["distances"][0][index]
    doc_id = resultate["ids"][0][index]

    print(f"\nTreffer {index + 1}")
    print(f"ID: {doc_id}")
    print(f"Distanz: {distance}")
    print(f"Text: {document}")