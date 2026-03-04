# Sécurité des réseaux IoT

## Description

Ce projet consiste à concevoir un système IoT permettant de surveiller des données environnementales (température et humidité) et de les transmettre vers un serveur pour stockage et visualisation. Le système utilise plusieurs Arduino équipés de capteurs DHT11 et communiquant via le module NRF24L01.

Les données collectées sont envoyées à un Arduino central qui les transmet à un serveur web développé avec Flask. Les informations sont ensuite enregistrées dans une base de données SQLite et peuvent être consultées via une interface web.

## Architecture du système

Le système est composé des éléments suivants :

* **Arduino esclave** : lit les données du capteur DHT11 (température et humidité).
* **Module NRF24L01** : permet la communication sans fil entre les Arduino.
* **Arduino central** : reçoit les données des Arduino esclaves et les transmet au serveur.
* **Serveur Flask** : traite les données reçues.
* **Base de données SQLite** : stocke les données environnementales.
* **Interface Web** : permet à l’administrateur de consulter les données.

## Fonctionnement

1. Le capteur **DHT11** mesure la température et l’humidité.
2. L’**Arduino esclave** lit les données du capteur.
3. Les données sont envoyées via **NRF24L01** vers l’**Arduino central**.
4. L’Arduino central transmet les données au **serveur Flask** via une requête HTTP.
5. Le serveur traite les données et les enregistre dans la **base de données SQLite**.
6. L’**administrateur** peut consulter les données depuis l’interface web.

## Technologies utilisées

* Arduino
* Capteur DHT11
* Module NRF24L01
* Python Flask
* SQLite
* HTTP (POST / GET)
* Interface Web

## Objectif du projet

* Collecter des données environnementales en temps réel.
* Transmettre les données à travers un réseau IoT.
* Stocker et visualiser les données via une interface web.
* Comprendre les mécanismes de communication dans les réseaux IoT.


Projet académique réalisé dans le cadre d’une étude sur la sécurité et les réseaux IoT.

