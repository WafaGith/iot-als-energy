# 4.3. Implementasi Perhitungan Double Exponential Smoothing (Holt)

Pada tahap ini, sistem akan melakukan peramalan (prediksi) total konsumsi energi listrik ke depannya menggunakan algoritma *Double Exponential Smoothing* atau yang sering dikenal dengan Metode Holt. Metode ini dipilih karena kemampuannya yang sangat baik dalam menangani data historis yang memiliki unsur tren naik-turun seiring berjalannya waktu, seperti halnya karakteristik pemakaian listrik di industri konveksi.

Berdasarkan pengujian simulasi sistem terhadap 81 kombinasi parameter yang mungkin, didapatkan bahwa nilai parameter yang menghasilkan tingkat *error* terkecil (paling akurat) untuk total pemakaian mesin ini adalah:
- **Parameter Alpha ($\alpha$) = 0.6** (untuk memberikan bobot pemulusan pada data aktual)
- **Parameter Beta ($\beta$) = 0.4** (untuk memberikan bobot pemulusan pada tren fluktuasi)

Untuk membuktikan bagaimana sistem komputer di balik layar memperoleh nilai peramalan tersebut, berikut dijabarkan proses perhitungan matematisnya secara manual. Sebagai contoh, diambil 4 hari pertama dari data historis total konsumsi energi (kWh):

- **Data Aktual Hari 1 ($Y_1$):** 2.216 kWh
- **Data Aktual Hari 2 ($Y_2$):** 3.373 kWh
- **Data Aktual Hari 3 ($Y_3$):** 3.646 kWh
- **Data Aktual Hari 4 ($Y_4$):** 3.520 kWh

---

### Tahap 1: Inisialisasi Nilai Awal
Sebelum rumus dapat berjalan secara iteratif (berulang-ulang), metode Holt membutuhkan pijakan nilai awal, yaitu nilai Level ($L$) dan Tren ($T$) untuk hari pertama. 

- **Nilai Level Awal ($L_1$):** Diambil langsung dari pemakaian aktual di hari pertama.
  $$L_1 = Y_1 = 2.216$$
- **Nilai Tren Awal ($T_1$):** Didapat dari selisih pemakaian antara hari kedua dengan hari pertama.
  $$T_1 = Y_2 - Y_1 = 3.373 - 2.216 = 1.157$$

---

### Tahap 2: Iterasi Hari Kedua
Saat data pemakaian hari kedua terekam ($Y_2 = 3.373$), sistem mulai memperbarui nilai Level dan Tren berdasarkan bobot parameter $\alpha$ dan $\beta$.

**a. Menghitung Level Baru ($L_2$)**
Sistem mengombinasikan data aktual hari ini dengan hasil level dan tren hari sebelumnya.
$$L_2 = \alpha Y_2 + (1 - \alpha) (L_1 + T_1)$$
$$L_2 = 0.6(3.373) + 0.4(2.216 + 1.157)$$
$$L_2 = 2.0238 + 0.4(3.373)$$
$$L_2 = 2.0238 + 1.3492 = 3.373$$

**b. Menghitung Tren Baru ($T_2$)**
Sistem juga mengukur seberapa besar pergerakan tren pemakaian dari hari kemarin ke hari ini.
$$T_2 = \beta (L_2 - L_1) + (1 - \beta) T_1$$
$$T_2 = 0.4(3.373 - 2.216) + 0.6(1.157)$$
$$T_2 = 0.4(1.157) + 0.6942$$
$$T_2 = 0.4628 + 0.6942 = 1.157$$

---

### Tahap 3: Iterasi Hari Ketiga dan Pengecekan *Error*
Pada hari ketiga, pemakaian aktual yang tercatat adalah $Y_3 = 3.646$ kWh. Melalui pemulusan data di hari sebelumnya, sistem sebenarnya sudah menyiapkan prediksi pemakaian untuk hari ketiga ini.

**a. Prediksi Pemakaian untuk Hari Ketiga ($F_3$)**
Hasil prediksi adalah penjumlahan dari pemulusan Level dan Tren hari sebelumnya.
$$F_3 = L_2 + T_2$$
$$F_3 = 3.373 + 1.157 = 4.530 \text{ kWh}$$

**b. Menghitung Tingkat Akurasi/Error (MAPE)**
Karena sistem memprediksi 4.530 kWh namun kenyataannya adalah 3.646 kWh, maka terdapat selisih (*error*). Berikut adalah perhitungan persentase simpangannya (*Absolute Percentage Error*):
$$APE_3 = \left| \frac{\text{Aktual} - \text{Prediksi}}{\text{Aktual}} \right| \times 100\%$$
$$APE_3 = \left| \frac{3.646 - 4.530}{3.646} \right| \times 100\% = 24.25\%$$
*(Tingkat error di awal proses wajar jika masih berfluktuasi cukup besar, dikarenakan algoritma masih dalam tahap awal mempelajari dan menyesuaikan diri dengan pola kelistrikan mesin).*

**c. Pembaruan Level ($L_3$) dan Tren ($T_3$)**
Agar prediksi esok hari menjadi lebih akurat, sistem memperbarui kembali rumusnya menggunakan rekaman data hari ini.
$$L_3 = 0.6(3.646) + 0.4(3.373 + 1.157) = 2.1876 + 1.8120 = 3.9996$$
$$T_3 = 0.4(3.9996 - 3.373) + 0.6(1.157) = 0.2506 + 0.6942 = 0.9448$$

**d. Prediksi untuk Esok Hari (Hari Ke-4)**
Setelah mendapatkan $L_3$ dan $T_3$, sistem langsung mengkalkulasi proyeksi pemakaian listrik untuk esok harinya.
$$F_4 = L_3 + T_3 = 3.9996 + 0.9448 = 4.9444 \text{ kWh}$$

Proses komputasi matematika di atas secara dinamis akan terus diulang oleh sistem untuk seluruh rentang waktu data historis. Hasil akhir proyeksi keseluruhan beserta nilai rata-rata persentase kesalahannya (MAPE) disajikan selengkapnya pada tabel rekapitulasi.
