"""
ml.scoring
==========
Mesin penilaian - yang memutuskan sebuah masukan berbahaya atau tidak.

    url.py         URL: daftar putih + aturan + dua model machine learning
    email.py       Email: header, isi surat, dan setiap tautan di dalamnya
    file.py        Berkas: analisis statis isi berkas
    deep_rules.py  Aturan atas bukti hasil membuka alamat

Pemisahan folder ini disengaja:

    ml/features/   MENGUKUR    - mengubah masukan mentah jadi angka
    ml/scoring/    MEMUTUSKAN  - mengubah angka jadi kesimpulan
    ml/training/   MELATIH     - menghasilkan berkas model
    ml/models/     MENYIMPAN   - berkas model dan daftar putih

Sebelumnya keempatnya bercampur: skrip pelatihan berada di folder yang sama
dengan berkas model, dan modul penilaian berserakan di akar ml/. Susunan itu
membuat orang sulit menebak berkas mana yang dijalankan dan berkas mana yang
hanya hasil.
"""
