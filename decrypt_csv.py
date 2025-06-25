import csv
from cryptography.fernet import Fernet

# Charger la clé Fernet
with open("key.txt", "rb") as f:
    fernet = Fernet(f.read())

with open("data/node_2_data.csv", "r") as f:
    reader = csv.reader(f)
    header = next(reader)

    for row in reader:
        try:
            # Si ligne chiffrée (format : node_id, data_encrypted, timestamp)
            if len(row) == 3 and row[1].startswith("gAAAAA"):
                decrypted = fernet.decrypt(row[1].encode()).decode()
                temperature, humidity = decrypted.split(',')
                print(f"🔓 Déchiffré → Node {row[0]} | Temp: {temperature}°C | Hum: {humidity}% | Time: {row[2]}")
            # Si ligne ancienne (claire)
            elif len(row) == 4:
                print(f"🟡 Donnée claire → Node {row[0]} | Temp: {row[1]}°C | Hum: {row[2]}% | Time: {row[3]}")
            else:
                print("⚠️ Ligne non reconnue :", row)
        except Exception as e:
            print("⛔ Erreur de déchiffrement :", row)
