import csv
from pathlib import Path

_CSV_PATH = Path(__file__).parent.parent / "data" / "kepmendagri-2022.csv"

_provinsi: dict[str, str] = {}   # kode 1-segmen -> nama
_kab_kota: dict[str, str] = {}   # kode 2-segmen -> nama
_kecamatan: dict[str, str] = {}  # kode 3-segmen -> nama
_kelurahan: dict[str, str] = {}  # kode 4-segmen (adm4) -> nama


def _load_wilayah_data() -> None:
    with open(_CSV_PATH, encoding="utf-8") as f:
        for kode, nama in csv.reader(f):
            kode, nama = kode.strip(), nama.strip()
            jumlah_segmen = kode.count(".") + 1
            if jumlah_segmen == 1:
                _provinsi[kode] = nama
            elif jumlah_segmen == 2:
                _kab_kota[kode] = nama
            elif jumlah_segmen == 3:
                _kecamatan[kode] = nama
            elif jumlah_segmen == 4:
                _kelurahan[kode] = nama


_load_wilayah_data()


LOKASI_TERDAFTAR = {
    "jakarta pusat": {"adm4": "31.71.03.1001", "nama_tampil": "Jakarta Pusat (Kemayoran)"},
    "jakarta selatan": {"adm4": "31.74.04.1006", "nama_tampil": "Jakarta Selatan (Pejaten Barat)"},
}

ALIAS_LOKASI = {
    "jaksel": "jakarta selatan",
    "jakpus": "jakarta pusat",
    "jaktim": "jakarta timur",
    "jakbar": "jakarta barat",
    "jakut": "jakarta utara",
    "jogja": "yogyakarta",
    "jogjakarta": "yogyakarta",
}


def _normalisasi(nama_daerah: str) -> str:
    key = nama_daerah.strip().lower()
    return ALIAS_LOKASI.get(key, key)


def _cari_kab_kota(query: str) -> list[tuple[str, str]]:
    q = query.strip().upper()
    return [(kode, nama) for kode, nama in _kab_kota.items() if q in nama.upper()]


def _cari_provinsi(query: str) -> list[tuple[str, str]]:
    q = query.strip().upper()
    return [(kode, nama) for kode, nama in _provinsi.items() if q in nama.upper()]


def _kab_kota_di_provinsi(kode_provinsi: str) -> list[tuple[str, str]]:
    return [(k, n) for k, n in _kab_kota.items() if k.startswith(kode_provinsi + ".")]


def _representative_adm4(kode_kab_kota: str) -> tuple[str, str] | None:
    kecamatan_di_bawahnya = sorted(k for k in _kecamatan if k.startswith(kode_kab_kota + "."))
    for kec_kode in kecamatan_di_bawahnya:
        kelurahan_di_bawahnya = sorted(k for k in _kelurahan if k.startswith(kec_kode + "."))
        if kelurahan_di_bawahnya:
            adm4 = kelurahan_di_bawahnya[0]
            return adm4, _kelurahan[adm4]
    return None


def resolve_location(nama_daerah: str) -> dict:
    nama_ternormalisasi = _normalisasi(nama_daerah)

    if nama_ternormalisasi in LOKASI_TERDAFTAR:
        data = LOKASI_TERDAFTAR[nama_ternormalisasi]
        return {"status": "found", "adm4": data["adm4"], "nama_tampil": data["nama_tampil"]}

    kandidat = _cari_kab_kota(nama_ternormalisasi)

    if len(kandidat) == 1:
        kode_kab_kota, nama_kab_kota = kandidat[0]
        representasi = _representative_adm4(kode_kab_kota)
        if representasi is None:
            return {"status": "not_found"}
        adm4, nama_kelurahan = representasi
        nama_tampil = f"{nama_kab_kota.title()} ({nama_kelurahan.title()})"
        return {"status": "found", "adm4": adm4, "nama_tampil": nama_tampil}

    if len(kandidat) > 1:
        opsi = sorted({nama.title() for _, nama in kandidat})
        return {"status": "ambiguous", "opsi": opsi}

    kandidat_provinsi = _cari_provinsi(nama_ternormalisasi)

    if len(kandidat_provinsi) == 0:
        return {"status": "not_found"}

    if len(kandidat_provinsi) > 1:
        opsi = sorted({nama.title() for _, nama in kandidat_provinsi})
        return {"status": "ambiguous", "opsi": opsi}

    kode_provinsi, _ = kandidat_provinsi[0]
    kota_list = _kab_kota_di_provinsi(kode_provinsi)
    if not kota_list:
        return {"status": "not_found"}

    opsi = sorted({nama.title() for _, nama in kota_list})
    return {"status": "ambiguous", "opsi": opsi}