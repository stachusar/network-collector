## Instrukcja Obsługi [Skryptu Pythonowego do Przetwarzania Danych](https://github.com/stachusar/network-collector/blob/main/spuber.py)
IF YOU WANT TO READ IN ENGLISH [click here](https://github.com/stachusar/network-collector/blob/main/README_EN.md)
#### Spis Treści
1. [Przegląd Skryptu](#1-przegląd-skryptu)
2. [Wymagania](#2-wymagania)
   - [2.1. Instalacja collectd](#21-instalacja-collectd)
     - [2.1.1. Systemy Debian/Ubuntu](#211-systemy-debianubuntu)
     - [2.1.2. Systemy RedHat/CentOS](#212-systemy-redhatcentos)
   - [2.2. Konfiguracja collectd](#22-konfiguracja-collectd)
     - [2.2.1. Znalezienie nazwy interfejsu sieciowego](#221-znalezienie-nazwy-interfejsu-sieciowego)
     - [2.2.2. Edytowanie pliku konfiguracyjnego](#222-edytowanie-pliku-konfiguracyjnego)
     - [2.2.3. Konfiguracja zbierania danych sieciowych](#223-konfiguracja-zbierania-danych-sieciowych)
   - [2.3. Restart collectd](#23-restart-collectd)
3. [Konfiguracja Skryptu](#3-konfiguracja-skryptu)
4. [Struktura Katalogów](#4-struktura-katalogów)
5. [Uruchomienie Skryptu](#5-uruchomienie-skryptu)
   - [5.1. Tworzenie Pliku Usługi Systemd (.service)](#51-tworzenie-pliku-usługi-systemd-service)
   - [5.2. Tworzenie Pliku Timera Systemd (.timer)](#52-tworzenie-pliku-timera-systemd-timer)
6. [Aktywacja i Uruchamianie](#6-aktywacja-i-uruchamianie)
7. [Monitoring i Logi](#7-monitoring-i-logi)
8. [Legenda pojęć](#8-legenda-pojęć)
### 1 Przegląd Skryptu
Ten skrypt służy do zbierania, przetwarzania i zapisywania danych statystycznych dotyczących ruchu sieciowego na serwerze Debian, używając plików RRD (`collectd`). Skrypt agreguje dane godzinowe, dzienne i miesięczne, a następnie zapisuje je do plików CSV. Możliwe jest także logowanie działań skryptu i opcjonalne wyświetlanie danych.
### 2. Wymagania
Instalacja i Konfiguracja collectd dla Monitorowania Sieci
collectd to system monitorowania wydajności, który gromadzi metryki z różnych źródeł i zapisuje je w różnych formatach, w tym w bazach danych typu Round-Robin (RRD). Aby monitorować interfejs sieciowy, tak jak ens3, musisz zainstalować i skonfigurować collectd w następujący sposób:
#### 2.1. Instalacja collectd
##### 2.1.1. Instalacja na systemach opartych na Debianie/Ubuntu:
Otwórz terminal i wpisz poniższe polecenie:
```bash
sudo apt-get update
sudo apt-get install collectd collectd-utils
```
##### 2.1.2. Instalacja na systemach opartych na RedHat/CentOS:
Użyj poniższego polecenia:
```bash
sudo yum install epel-release
sudo yum install collectd
```
### 2.2. Konfiguracja collectd
#### 2.2.1 Znalezienie nazwy interfejsu sieciowego
Aby sprawdzić nazwę swojego interfejsu sieciowego na systemie operacyjnym Linux, możesz skorzystać z polecenie ip. Pozwala na wyświetlenie szczegółowych informacji o wszystkich interfejsach sieciowych w systemie. 
Aby wyświetlić listę wszystkich aktywnych interfejsów, użyj:
```bash
ip link show
```
lub w skróconej formie:
```bash 
ip a
```
Wynik polecenia pokaże listę interfejsów wraz z przypisanymi im adresami IP oraz dodatkowymi informacjami. Nazwy interfejsów zazwyczaj znajdziesz w pierwszej kolumnie (np. ens33, eth0, wlan0).
#### 2.2.2. Edytowanie pliku konfiguracyjnego
Plik konfiguracyjny collectd zwykle znajduje się w /etc/collectd/collectd.conf.  
 Otwórz ten plik w edytorze tekstu:
```bash

sudo nano /etc/collectd/collectd.conf
```
#### 2.2.3. Konfiguracja zbierania danych sieciowych:
Aby zbierać dane z interfejsu sieciowego, musisz aktywować plugin interface oraz rrdtool w pliku collectd.conf.   
Dodaj lub odkomentuj następujące sekcje:
```bash
LoadPlugin interface
LoadPlugin rrdtool
<Plugin "interface">
  Interface "ens3" #nazwy interfejsu mogą być różne 
  IgnoreSelected false
</Plugin>
<Plugin rrdtool>
  DataDir "/var/lib/collectd/rrd/"
  CacheFlush 120
</Plugin>
```
W powyższej konfiguracji, Interface "ens3" mówi collectd, aby zbierał dane z interfejsu ens3. DataDir wskazuje katalog, gdzie collectd będzie zapisywać dane RRD.
#### 2.3 Restart collectd:
Po zakończeniu konfiguracji zrestartuj usługę collectd, aby zmiany weszły w życie:
```bash
sudo systemctl restart collectd
```
### 3. Konfiguracja Skryptu
Skonfiguruj następujące zmienne przed uruchomieniem skryptu:
- `RRD_DIR`: Ścieżka do katalogu z plikami RRD.
- `STATISTIC_DIR`: Ścieżka do katalogu na przetworzone dane statystyczne.
- `LOG_DIR`: Ścieżka do katalogu na logi działania skryptu.
- `TEST_MODE`: Ustawienie `True` umożliwia testowe wyświetlanie danych, `False` aktywuje normalny tryb pracy.
### 4. Struktura Katalogów
Skrypt automatycznie tworzy niezbędne katalogi dla danych i logów.
### 5. Uruchomienie Skryptu
Skrypt można uruchamiać ręcznie lub automatycznie za pomocą `systemd`.
#### 5.1. Tworzenie Pliku Usługi Systemd (.service)
1. Utwórz plik `data_processing.service` w `/etc/systemd/system/`.
2. Zawartość pliku:
```ini
[Unit]
Description=Przetwarzanie danych statystycznych
[Service]
Type=simple
ExecStart=/usr/bin/python3 /ścieżka/do/skryptu.py
User=ubuntu
Group=ubuntu
[Install]
WantedBy=multi-user.target
```
#### 5.2. Tworzenie Pliku Timera Systemd (.timer)
1. Utwórz plik data_processing.timer w /etc/systemd/system/.
2. Zawartość pliku:
```ini
Copy code
[Unit]
Description=Uruchamia przetwarzanie danych co godzinę
[Timer]
OnCalendar=hourly

Persistent=true
[Install]
WantedBy=timers.target
```
### 6. Aktywacja i Uruchamianie
Aktywuj i uruchom timer:
```bash
sudo systemctl daemon-reload
sudo systemctl enable data_processing.timer
sudo systemctl start data_processing.timer
```
### 7. Monitoring i Logi
Logi działania skryptu znajdują się w LOG_DIR.  
Sprawdź status usługi: 
```
systemctl status data_processing.service.
```
Dzięki tej dokumentacji możesz efektywnie wykorzystać skrypt w swoim systemie, zarządzając regularnym przetwarzaniem danych.
### 8. Legenda pojęć 
Kilka kluczowych terminów i elementów używanych w tym dokumencie:
- **Interfejs sieciowy**: Port sieciowy w komputerze, który umożliwia komunikację z innymi urządzeniami w sieci.
- **`collectd`**: Daemon systemowy, który gromadzi metryki z różnych źródeł i zapisuje je w bazach danych typu Round-Robin (RRD).
- **RRD (Round-Robin Database)**: Format bazy danych, który przechowuje zmienne numeryczne; używany głównie do gromadzenia danych o wydajności.
- **Plugin**: Dodatek do `collectd`, który rozszerza jego funkcjonalność, umożliwiając zbieranie danych z różnych źródeł, w tym z interfejsów sieciowych.
- **Systemd**: System i usługa menedżera dla systemów operacyjnych Linux, który umożliwia zarządzanie usługami systemowymi.
- **Service file (.service)**: Plik konfiguracyjny dla `systemd`, który określa, jak usługa powinna być uruchamiana.
- **Timer file (.timer)**: Plik konfiguracyjny dla `systemd`, który definiuje harmonogram uruchamiania usługi.
- **Daemon**: Program komputerowy w systemie Unix, który działa w tle, zazwyczaj bez bezpośredniej interakcji z użytkownikiem.
---
