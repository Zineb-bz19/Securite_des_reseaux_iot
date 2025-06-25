import requests
from datetime import datetime

# Adresse de ton serveur Flask
url = "http://localhost:5000/api/sensor_data"

# Exemple de données
data = {
    "node_id": 2,
    "temperature": 33.3,
    "humidity": 30.0,
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

# Envoi POST
response = requests.post(url, json=data)

# Affichage résultat
print("Réponse du serveur :")
print(response.status_code)
print(response.json())
