#!/usr/bin/env python3
"""Bir şehrin anlık hava durumunu ve birkaç günlük tahminini gösterir.

Veri kaynağı: Open-Meteo (https://open-meteo.com) — API anahtarı gerekmez.

Kullanım:
    python3 hava_durumu.py İstanbul
    python3 hava_durumu.py Ankara --gun 5
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO hava kodları -> (açıklama, emoji)
HAVA_KODLARI = {
    0: ("Açık", "☀️"),
    1: ("Çoğunlukla açık", "🌤️"),
    2: ("Parçalı bulutlu", "⛅"),
    3: ("Kapalı", "☁️"),
    45: ("Sisli", "🌫️"),
    48: ("Kırağılı sis", "🌫️"),
    51: ("Hafif çisenti", "🌦️"),
    53: ("Çisenti", "🌦️"),
    55: ("Yoğun çisenti", "🌧️"),
    56: ("Dondurucu çisenti", "🌧️"),
    57: ("Yoğun dondurucu çisenti", "🌧️"),
    61: ("Hafif yağmur", "🌦️"),
    63: ("Yağmur", "🌧️"),
    65: ("Şiddetli yağmur", "🌧️"),
    66: ("Dondurucu yağmur", "🌧️"),
    67: ("Şiddetli dondurucu yağmur", "🌧️"),
    71: ("Hafif kar", "🌨️"),
    73: ("Kar", "🌨️"),
    75: ("Yoğun kar", "❄️"),
    77: ("Kar taneleri", "🌨️"),
    80: ("Hafif sağanak", "🌦️"),
    81: ("Sağanak", "🌧️"),
    82: ("Şiddetli sağanak", "⛈️"),
    85: ("Hafif kar sağanağı", "🌨️"),
    86: ("Yoğun kar sağanağı", "❄️"),
    95: ("Gök gürültülü fırtına", "⛈️"),
    96: ("Dolu ile fırtına", "⛈️"),
    99: ("Şiddetli dolulu fırtına", "⛈️"),
}

GUNLER = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]


def json_getir(url, parametreler):
    tam_url = f"{url}?{urllib.parse.urlencode(parametreler)}"
    with urllib.request.urlopen(tam_url, timeout=10) as yanit:
        return json.load(yanit)


def sehir_bul(sehir):
    veri = json_getir(GEOCODING_URL, {"name": sehir, "count": 1, "language": "tr"})
    sonuclar = veri.get("results")
    if not sonuclar:
        return None
    return sonuclar[0]


def hava_getir(enlem, boylam, gun):
    return json_getir(FORECAST_URL, {
        "latitude": enlem,
        "longitude": boylam,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
                   "wind_speed_10m,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                 "precipitation_probability_max",
        "timezone": "auto",
        "forecast_days": gun,
    })


def kod_aciklama(kod):
    return HAVA_KODLARI.get(kod, ("Bilinmiyor", "❔"))


def gun_adi(tarih):
    from datetime import date
    return GUNLER[date.fromisoformat(tarih).weekday()]


def main():
    ayrac = argparse.ArgumentParser(description="Hava durumu gösterici")
    ayrac.add_argument("sehir", nargs="+", help="Şehir adı (ör. İstanbul)")
    ayrac.add_argument("--gun", type=int, default=3, choices=range(1, 17),
                       metavar="1-16", help="Tahmin gün sayısı (varsayılan: 3)")
    args = ayrac.parse_args()
    sehir_adi = " ".join(args.sehir)

    try:
        konum = sehir_bul(sehir_adi)
        if konum is None:
            print(f"'{sehir_adi}' bulunamadı.", file=sys.stderr)
            return 1
        veri = hava_getir(konum["latitude"], konum["longitude"], args.gun)
    except OSError as hata:
        print(f"Bağlantı hatası: {hata}", file=sys.stderr)
        return 1

    simdi = veri["current"]
    aciklama, emoji = kod_aciklama(simdi["weather_code"])
    yer = ", ".join(p for p in (konum.get("name"), konum.get("admin1"),
                                 konum.get("country")) if p)

    print(f"\n📍 {yer}")
    print(f"{emoji}  {aciklama}, {simdi['temperature_2m']:.0f}°C "
          f"(hissedilen {simdi['apparent_temperature']:.0f}°C)")
    print(f"💧 Nem: %{simdi['relative_humidity_2m']}   "
          f"💨 Rüzgar: {simdi['wind_speed_10m']:.0f} km/s")

    gunluk = veri["daily"]
    print(f"\n📅 {args.gun} günlük tahmin:")
    for i, tarih in enumerate(gunluk["time"]):
        acik, em = kod_aciklama(gunluk["weather_code"][i])
        yagis = gunluk["precipitation_probability_max"][i]
        yagis_metni = f"  ☔ %{yagis}" if yagis is not None else ""
        print(f"  {gun_adi(tarih)} {tarih[8:]}.{tarih[5:7]}  {em}  "
              f"{gunluk['temperature_2m_min'][i]:>3.0f}° / "
              f"{gunluk['temperature_2m_max'][i]:>3.0f}°  {acik}{yagis_metni}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
