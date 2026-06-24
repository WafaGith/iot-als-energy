# 4.3. Implementasi Metode Double Exponential Smoothing (Holt)

Pada penelitian ini, prediksi konsumsi energi listrik dilakukan menggunakan algoritma *Holt's Double Exponential Smoothing*. Metode ini dipilih karena kemampuannya dalam menangani data historis yang memiliki unsur tren. Berdasarkan hasil pengujian (*Trial and Error*) terhadap 81 kombinasi parameter, didapatkan parameter paling optimal untuk data konsumsi energi pada alat ini, yaitu:
- **Parameter Pemulusan Data (Alpha / $\alpha$) = 0.6**
- **Parameter Pemulusan Tren (Beta / $\beta$) = 0.4**

Berikut adalah penjabaran langkah-langkah perhitungan secara manual (matematis) untuk membuktikan cara kerja sistem berdasarkan sampel data historis konsumsi energi (kWh) harian.

## 4.3.1. Sampel Data Historis (Data Awal)
Berikut adalah cuplikan 4 data harian pertama yang terekam pada sistem:
- **Hari ke-1 ($Y_1$):** 2.216 kWh
- **Hari ke-2 ($Y_2$):** 3.373 kWh
- **Hari ke-3 ($Y_3$):** 3.646 kWh
- **Hari ke-4 ($Y_4$):** 3.520 kWh

---

## 4.3.2. Inisialisasi Nilai Awal (Periode ke-1)
Untuk memulai perhitungan, metode Holt memerlukan nilai pemulusan level awal ($L_1$) dan pemulusan tren awal ($T_1$). Sesuai kaidah standar, nilai diinisialisasi sebagai berikut:
- **Level Awal ($L_1$):** Diambil dari data aktual hari pertama.
  $$L_1 = Y_1 = 2.216$$
- **Tren Awal ($T_1$):** Dihitung dari selisih antara data aktual hari kedua dengan data hari pertama.
  $$T_1 = Y_2 - Y_1 = 3.373 - 2.216 = 1.157$$

---

## 4.3.3. Iterasi Perhitungan Periode ke-2
Pada periode ini, sistem melakukan pembaruan terhadap nilai *Level* dan *Trend* berdasarkan masuknya data historis baru ($Y_2 = 3.373$).

**1. Pemulusan Level ($L_2$)**
$$L_2 = \alpha Y_2 + (1 - \alpha) (L_1 + T_1)$$
$$L_2 = 0.6(3.373) + (1 - 0.6)(2.216 + 1.157)$$
$$L_2 = 2.0238 + 0.4(3.373)$$
$$L_2 = 2.0238 + 1.3492 = 3.373$$

**2. Pemulusan Tren ($T_2$)**
$$T_2 = \beta (L_2 - L_1) + (1 - \beta) T_1$$
$$T_2 = 0.4(3.373 - 2.216) + (1 - 0.4)(1.157)$$
$$T_2 = 0.4(1.157) + 0.6(1.157)$$
$$T_2 = 0.4628 + 0.6942 = 1.157$$

---

## 4.3.4. Iterasi Perhitungan Periode ke-3 & Perhitungan Error
Pada hari ke-3 (Data aktual $Y_3 = 3.646$), nilai prediksi (*Forecast*) untuk hari tersebut dihitung menggunakan hasil pemulusan pada akhir hari ke-2.

**1. Hasil Prediksi untuk Hari ke-3 ($F_3$)**
$$F_3 = L_2 + T_2$$
$$F_3 = 3.373 + 1.157 = 4.530 \text{ kWh}$$

**2. Perhitungan Akurasi/Error (APE Hari ke-3)**
Nilai *Absolute Percentage Error* (APE) mengukur seberapa jauh melesetnya prediksi terhadap data aktual yang terjadi.
$$APE_3 = \left| \frac{Y_3 - F_3}{Y_3} \right| \times 100\%$$
$$APE_3 = \left| \frac{3.646 - 4.530}{3.646} \right| \times 100\%$$
$$APE_3 = \left| \frac{-0.884}{3.646} \right| \times 100\% = 24.25\%$$
*Tingkat error pada awal iterasi umumnya masih cukup besar karena metode belum cukup "belajar" dari pola tren jangka panjang.*

**3. Pembaruan Level ($L_3$)**
$$L_3 = \alpha Y_3 + (1 - \alpha) (L_2 + T_2)$$
$$L_3 = 0.6(3.646) + 0.4(4.530)$$
$$L_3 = 2.1876 + 1.8120 = 3.9996$$

**4. Pembaruan Tren ($T_3$)**
$$T_3 = \beta (L_3 - L_2) + (1 - \beta) T_2$$
$$T_3 = 0.4(3.9996 - 3.373) + 0.6(1.157)$$
$$T_3 = 0.4(0.6266) + 0.6942$$
$$T_3 = 0.2506 + 0.6942 = 0.9448$$

**5. Proyeksi Prediksi Hari ke-4 ($F_4$)**
$$F_4 = L_3 + T_3$$
$$F_4 = 3.9996 + 0.9448 = 4.9444 \text{ kWh}$$

*(Catatan: Proses komputasi berlanjut secara otomatis hingga data terakhir (hari ke-30). Keseluruhan hasil rekapitulasi peramalan dan rata-rata perhitungan error (MAPE) disajikan lebih lanjut pada tabel rekapitulasi perhitungan di lampiran).*
