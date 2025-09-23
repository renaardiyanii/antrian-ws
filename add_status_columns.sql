-- Script untuk menambahkan kolom status dan waktu_panggil ke tabel antrian_admisi

-- Tambahkan kolom status
ALTER TABLE antrian_admisi
ADD COLUMN IF NOT EXISTS status VARCHAR(20);

-- Tambahkan kolom waktu_panggil
ALTER TABLE antrian_admisi
ADD COLUMN IF NOT EXISTS waktu_panggil TIMESTAMP;

-- Set default value untuk status yang sudah ada
UPDATE antrian_admisi
SET status = 'menunggu'
WHERE status IS NULL;

-- Berikan komentar pada kolom baru
COMMENT ON COLUMN antrian_admisi.status IS 'Status antrian: menunggu, dipanggil, processed, selesai';
COMMENT ON COLUMN antrian_admisi.waktu_panggil IS 'Waktu antrian dipanggil';