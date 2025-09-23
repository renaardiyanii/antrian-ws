-- Migration Script untuk menambahkan kolom loket dan status ke tabel antrian_admisi
-- Jalankan script ini di database PostgreSQL

-- Cek apakah kolom loket sudah ada, jika belum tambahkan
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'antrian_admisi' AND column_name = 'loket'
    ) THEN
        ALTER TABLE antrian_admisi ADD COLUMN loket VARCHAR(10) DEFAULT NULL;
        RAISE NOTICE 'Kolom loket ditambahkan ke tabel antrian_admisi';
    ELSE
        RAISE NOTICE 'Kolom loket sudah ada di tabel antrian_admisi';
    END IF;
END
$$;

-- Cek apakah kolom status sudah ada, jika belum tambahkan
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'antrian_admisi' AND column_name = 'status'
    ) THEN
        ALTER TABLE antrian_admisi ADD COLUMN status VARCHAR(20) DEFAULT 'menunggu';
        RAISE NOTICE 'Kolom status ditambahkan ke tabel antrian_admisi';
    ELSE
        RAISE NOTICE 'Kolom status sudah ada di tabel antrian_admisi';
    END IF;
END
$$;

-- Cek apakah kolom waktu_panggil sudah ada, jika belum tambahkan
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'antrian_admisi' AND column_name = 'waktu_panggil'
    ) THEN
        ALTER TABLE antrian_admisi ADD COLUMN waktu_panggil TIMESTAMP DEFAULT NULL;
        RAISE NOTICE 'Kolom waktu_panggil ditambahkan ke tabel antrian_admisi';
    ELSE
        RAISE NOTICE 'Kolom waktu_panggil sudah ada di tabel antrian_admisi';
    END IF;
END
$$;

-- Tambahkan indeks untuk performa yang lebih baik
CREATE INDEX IF NOT EXISTS idx_antrian_admisi_loket ON antrian_admisi(loket);
CREATE INDEX IF NOT EXISTS idx_antrian_admisi_status ON antrian_admisi(status);
CREATE INDEX IF NOT EXISTS idx_antrian_admisi_waktu_panggil ON antrian_admisi(waktu_panggil);

-- Tampilkan struktur tabel setelah migration
-- SELECT
--     column_name,
--     data_type,
--     character_maximum_length,
--     is_nullable,
--     column_default
-- FROM information_schema.columns
-- WHERE table_name = 'antrian_admisi'
-- ORDER BY ordinal_position;


-- Script untuk cek dan migrate database antrian_admisi
-- Jalankan script ini di database PostgreSQL

-- Cek apakah kolom loket sudah ada, jika belum tambahkan
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'antrian_admisi' AND column_name = 'loket'
    ) THEN
        ALTER TABLE antrian_admisi ADD COLUMN loket VARCHAR(10) DEFAULT NULL;
        RAISE NOTICE 'Kolom loket ditambahkan ke tabel antrian_admisi';
    ELSE
        RAISE NOTICE 'Kolom loket sudah ada di tabel antrian_admisi';
    END IF;
END
$$;

-- Cek apakah kolom status sudah ada, jika belum tambahkan
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'antrian_admisi' AND column_name = 'status'
    ) THEN
        ALTER TABLE antrian_admisi ADD COLUMN status VARCHAR(20) DEFAULT 'menunggu';
        RAISE NOTICE 'Kolom status ditambahkan ke tabel antrian_admisi';
    ELSE
        RAISE NOTICE 'Kolom status sudah ada di tabel antrian_admisi';
    END IF;
END
$$;

-- Cek apakah kolom waktu_panggil sudah ada, jika belum tambahkan
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'antrian_admisi' AND column_name = 'waktu_panggil'
    ) THEN
        ALTER TABLE antrian_admisi ADD COLUMN waktu_panggil TIMESTAMP DEFAULT NULL;
        RAISE NOTICE 'Kolom waktu_panggil ditambahkan ke tabel antrian_admisi';
    ELSE
        RAISE NOTICE 'Kolom waktu_panggil sudah ada di tabel antrian_admisi';
    END IF;
END
$$;

-- Cek apakah kolom waktu_update sudah ada, jika belum tambahkan
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'antrian_admisi' AND column_name = 'waktu_update'
    ) THEN
        ALTER TABLE antrian_admisi ADD COLUMN waktu_update TIMESTAMP DEFAULT NULL;
        RAISE NOTICE 'Kolom waktu_update ditambahkan ke tabel antrian_admisi';
    ELSE
        RAISE NOTICE 'Kolom waktu_update sudah ada di tabel antrian_admisi';
    END IF;
END
$$;

-- Update data yang sudah ada untuk memiliki status default
UPDATE antrian_admisi
SET status = 'menunggu'
WHERE status IS NULL OR status = '';

-- Tambahkan indeks untuk performa yang lebih baik
CREATE INDEX IF NOT EXISTS idx_antrian_admisi_loket ON antrian_admisi(loket);
CREATE INDEX IF NOT EXISTS idx_antrian_admisi_status ON antrian_admisi(status);
CREATE INDEX IF NOT EXISTS idx_antrian_admisi_tgl_status ON antrian_admisi(tgl_kunjungan, status);
CREATE INDEX IF NOT EXISTS idx_antrian_admisi_waktu_panggil ON antrian_admisi(waktu_panggil);
CREATE INDEX IF NOT EXISTS idx_antrian_admisi_waktu_update ON antrian_admisi(waktu_update);

-- Cek struktur tabel setelah migration
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'antrian_admisi'
ORDER BY ordinal_position;