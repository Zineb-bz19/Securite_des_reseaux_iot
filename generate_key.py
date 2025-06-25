from cryptography.fernet import Fernet

# Générer une clé Fernet
key = Fernet.generate_key()

# L'afficher à l'écran
print("✅ Clé générée :")
print(key.decode())

# Sauvegarder dans un fichier key.txt
with open("key.txt", "wb") as f:
    f.write(key)

print("🔐 Clé enregistrée dans key.txt")
