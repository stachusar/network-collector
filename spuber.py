import pandas as pd
import numpy as np
import subprocess
import os
import csv
import warnings
from datetime import datetime

# Ignoruj ostrzeżenia FutureWarning
warnings.simplefilter(action='ignore', category=FutureWarning)

RRD_DIR = "/var/lib/collectd/rrd/debian/interface-ens3"
STATISTIC_DIR = "/home/ubuntu/statistic"
LOG_DIR="/home/ubuntu"
TEST_MODE = False

def log_and_display(data, message, display=False):
    # Logowanie do pliku zawsze
    save_log(message, 'INFO')

    # Warunkowe wyświetlanie komunikatów i danych
    print(message)  # Wyświetla komunikat logu
    if display:
        for df in data:
            if not df.empty:
                print(df)  # Wyświetla DataFrame, jeśli nie jest pusty

def save_log(message, log_type='INFO'):
    log_dir = os.path.join(LOG_DIR, "log")
    os.makedirs(log_dir, exist_ok=True)  # Tworzenie katalogu logów, jeśli nie istnieje
    log_filename = "SPUBer.log"
    log_path = os.path.join(log_dir, log_filename)
    with open(log_path, "a") as logfile:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        logfile.write(f"[{timestamp}] [{log_type}] {message}\n")


def generate_directory_structure():
    current_year = datetime.now().year
    spub_dir = os.path.join(STATISTIC_DIR, "SPUB")
    os.makedirs(spub_dir, exist_ok=True)
    year_dir = os.path.join(spub_dir, str(current_year))
    os.makedirs(year_dir, exist_ok=True)
    return spub_dir, year_dir # Upewnij się, że ta linia istnieje i zawsze jest wykonana

def convert_units(bytes_col):
    """Convert bytes values to readable units or handle NaN."""
    if pd.isna(bytes_col):
        return "N/A"
    if bytes_col > 1e15:
        return f"{bytes_col / 1e15:.2f} PB"
    elif bytes_col > 1e12:
        return f"{bytes_col / 1e12:.2f} TB"
    elif bytes_col > 1e9:
        return f"{bytes_col / 1e9:.2f} GB"
    elif bytes_col > 1e6:
        return f"{bytes_col / 1e6:.2f} MB"
    elif bytes_col > 1e3:
        return f"{bytes_col / 1e3:.2f} KB"
    return f"{bytes_col} B"

def convert_to_bytes(size_str):
    """Konwertuje czytelne jednostki danych na bajty."""
    if isinstance(size_str, float) or isinstance(size_str, int):
        # Jeśli wartość jest już liczbowym typem danych, zakładamy, że jest to bajty
        return size_str
    units = {"B": 1, "KB": 1e3, "MB": 1e6, "GB": 1e9, "TB": 1e12, "PB": 1e15}
    size_str = size_str.upper().replace(" ", "")  # Usuń spacje i zamień na wielkie litery
    num = float(''.join(filter(str.isdigit or str.isspace or str == '.', size_str)))
    unit = ''.join(filter(str.isalpha, size_str))
    
    if unit in units:
        return num * units[unit]
    else:
        raise ValueError("Nieznana jednostka w rozmiarze danych.")

def fetch_rrd_data(rrd_file, start_date='now-7d'):
    rrd_path = os.path.join(RRD_DIR, rrd_file)
    try:
        # Wywołanie polecenia rrdtool fetch
        command = f"rrdtool fetch {rrd_path} AVERAGE --start {start_date} --end now --resolution 3600"
        process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if process.returncode != 0:
            print(f"Błąd podczas wywoływania polecenia rrdtool fetch dla pliku {rrd_file}: {process.stderr}")
            return None
        else:
            return process.stdout
    except Exception as e:
        print(f"Wystąpił wyjątek podczas pobierania danych z pliku RRD {rrd_file}: {e}")
        return None

def process_rrd_output(output):
    lines = output.strip().split("\n")
    data = []
    for line in lines[2:]:  # Skip the first two lines of headers
        parts = line.split(": ")
        if len(parts) < 2:
            continue
        timestamp, values = parts[0], parts[1].split(" ")
        rx, tx = float(values[0]), float(values[1])
        data.append([int(timestamp), rx, tx])
    return pd.DataFrame(data, columns=['Timestamp', 'RX', 'TX'])

def find_start_date_from_data(df):
    # Przetwarzanie df w celu znalezienia daty początkowej
    df['NonZero'] = (df['RX'] != '0.0 B') | (df['TX'] != '0.0 B')
    start_index = df.index[df['NonZero'] & ~df['NonZero'].shift(1).fillna(False)]
    if not start_index.empty:
        return df.loc[start_index[0], df.columns[0]]  # Pobierz pierwszą kolumnę DataFrame'u
    return None

def aggregate_and_display_hourly_rrd_data(display=True, save_to_file=False):
    for rrd_file in os.listdir(RRD_DIR):
        if not rrd_file.endswith(".rrd") or "if_octets" not in rrd_file:
            continue
        output = fetch_rrd_data(rrd_file)
        if output:
            df = process_rrd_output(output)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
            df.set_index('Timestamp', inplace=True)

            df['Nonzero'] = (df['RX'] > 0.0) | (df['TX'] > 0.0)

            if df['Nonzero'].any():
                start_date = df[df['Nonzero']].index[0]
                df_filtered = df.loc[start_date:]

                grouped = df_filtered.groupby(df_filtered.index.date)
                for date, group in grouped:
                    print(f"Dane godzinowe dla {rrd_file.replace('.rrd', '')} - {date}:")
                    print("Date        Recive         Transfer")

                    df_resampled = group.resample('H').sum()
                    df_resampled = df_resampled[(df_resampled['RX'] > 0.0) | (df_resampled['TX'] > 0.0)]
                    df_resampled['RX'] = df_resampled['RX'].apply(convert_units)
                    df_resampled['TX'] = df_resampled['TX'].apply(convert_units)
                    
                    if df_resampled.empty:
                        print("Brak danych dla tej doby.")
                    else:
                        for hour, row in df_resampled.iterrows():
                            print(f"{hour.strftime('%Y-%m-%d %H:%M')}  {row['RX']}  {row['TX']}")
                    
                    print("\n")  # Dodatkowa linia dla czytelności
            else:
                print(f"Nie znaleziono niezerowych danych dla {rrd_file}.")
            print("\n")
        else:
            print(f"Nie znaleziono danych dla pliku {rrd_file}.")

def aggregate_and_display_daily_rrd_data(display=True, save_to_file=False):
    aggregated_data_frames = []
    for rrd_file in os.listdir(RRD_DIR):
        if not rrd_file.endswith(".rrd") or "if_octets" not in rrd_file:
            continue
        output = fetch_rrd_data(rrd_file)
        if output:
            df = process_rrd_output(output)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
            df.set_index('Timestamp', inplace=True)
            df_non_zero = df[(df['RX'] != 0) | (df['TX'] != 0)]
            if not df_non_zero.empty:
                df_daily = df_non_zero.resample('D').sum()
                df_daily = df_daily[(df_daily['RX'] != 0) | (df_daily['TX'] != 0)]
                df_daily['RX'] = df_daily['RX'].apply(convert_units)
                df_daily['TX'] = df_daily['TX'].apply(convert_units)
                df_daily.index = df_daily.index.to_period('D')
                aggregated_data_frames.append(df_daily)
                if display:
                    month = df_daily.index[0].strftime('%Y-%m')
                    print(f"Daily data for {rrd_file.replace('.rrd', '')} - {month}:")
                    print("Date       Receive        Transfer")
                    for index, row in df_daily.iterrows():
                        print(f"{index}  {row['RX']}  {row['TX']}")
    if save_to_file:
        return aggregated_data_frames

def save_daily_data_to_file(aggregated_data_frames):
    # Rozpakowanie spub_dir i year_dir z wyniku generate_directory_structure
    spub_dir, year_dir = generate_directory_structure()

    for df_daily in aggregated_data_frames:
        if not df_daily.empty:
            year_month = df_daily.index[0].strftime('%Y-%m')
            filename = f"SPUB_{year_month}.csv"
            # Używamy year_dir do stworzenia pełnej ścieżki pliku
            file_path = os.path.join(year_dir, filename)
            df_daily.to_csv(file_path, index_label='Date')
            print(f"Saved data to {file_path}")


def archive_daily_data():
    # Pobierz bieżącą datę
    current_date = datetime.now()
    last_month = (current_date.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')  # Ostatni miesiąc
    year = last_month.split('-')[0]

    spub_dir, year_dir = generate_directory_structure()
    tar_filename = f"daily_data_{last_month}.tar.gz"
    tar_path = os.path.join(spub_dir, tar_filename)

    with tarfile.open(tar_path, "w:gz") as tar:
        for file in os.listdir(year_dir):
            if file.startswith("SPUB_" + last_month):
                file_path = os.path.join(year_dir, file)
                tar.add(file_path, arcname=os.path.basename(file_path))
                os.remove(file_path)  # Usuń plik po dodaniu do archiwum
    print(f"Zarchiwizowano dane dziennie do {tar_path}")

def aggregate_and_display_monthly_rrd_data(display=True, save_to_file=False):
    aggregated_data_frames = []
    for rrd_file in os.listdir(RRD_DIR):
        if not rrd_file.endswith(".rrd") or "if_octets" not in rrd_file:
            continue
        output = fetch_rrd_data(rrd_file)
        if output:
            df = process_rrd_output(output)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
            df.set_index('Timestamp', inplace=True)

            df_non_zero = df[(df['RX'] != 0) | (df['TX'] != 0)]
            if not df_non_zero.empty:
                df_monthly = df_non_zero.resample('M').sum()
                df_monthly = df_monthly[(df_monthly['RX'] != 0) | (df_monthly['TX'] != 0)]
                df_monthly['RX'] = df_monthly['RX'].apply(convert_units)
                df_monthly['TX'] = df_monthly['TX'].apply(convert_units)
                df_monthly.index = df_monthly.index.to_period('M')
                
                # Dodaj DataFrame do listy, która może być zwrócona
                aggregated_data_frames.append(df_monthly)
                
                if display:
                    year = df_monthly.index[0].year
                    print(f"Monthly data for {rrd_file.replace('.rrd', '')} - {year}:")
                    print("Date      Receive         Transfer")
                    for index, row in df_monthly.iterrows():
                        print(f"{index}  {row['RX']}  {row['TX']}")

    # Zwracanie danych jeśli save_to_file jest ustawione na True
    if save_to_file:
        return aggregated_data_frames


def save_monthly_data_to_file(aggregated_data_frames):
    spub_dir, _ = generate_directory_structure()  # Rozpakowanie katalogu SPUB

    for df_monthly in aggregated_data_frames:
        if not df_monthly.empty:
            year = df_monthly.index[0].strftime('%Y')
            filename = f"SPUB_{year}.csv"
            file_path = os.path.join(spub_dir, filename)  # Zapisz w katalogu SPUB
            df_monthly.to_csv(file_path, index_label='Date')
            print(f"Saved monthly data to {file_path}")

def main():
    if TEST_MODE:
        log_and_display([], "TEST_MODE = True - Rozpoczęcie pracy skryptu", display=True)
        aggregate_and_display_hourly_rrd_data(display=True)
        aggregate_and_display_daily_rrd_data(display=True)
        aggregate_and_display_monthly_rrd_data(display=True)
        log_and_display([], "TEST_MODE = True - Zakończenie pracy skryptu", display=True)
    else:
        log_and_display([], "TEST_MODE = False - Rozpoczęcie pracy skryptu", display=True)
        generate_directory_structure()
        aggregated_data = aggregate_and_display_daily_rrd_data(display=False, save_to_file=True)
        if aggregated_data:
            save_daily_data_to_file(aggregated_data)
            log_and_display(aggregated_data, "Zapisano dane dziennie.", display=True)

        aggregated_monthly_data = aggregate_and_display_monthly_rrd_data(display=False, save_to_file=True)
        if aggregated_monthly_data:
            save_monthly_data_to_file(aggregated_monthly_data)
            log_and_display(aggregated_monthly_data, "Zapisano dane miesięczne.", display=True)

        log_and_display([], "TEST_MODE = False - Zakończenie pracy skryptu", display=True)

if __name__ == "__main__":
    main()
