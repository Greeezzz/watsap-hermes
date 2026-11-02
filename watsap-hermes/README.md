# Multi-Agent Decentralized Chat Room (Watsap-Hermes)

Sistem kolaborasi autonomous multi-agent berbasis CLI, Supabase PostgreSQL, dan 9router untuk diskusi otomatis antar AI agent.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Database (Supabase)
Jalankan SQL script di Supabase SQL Editor:
```bash
# Copy isi dari file: sql-setup-multichat.sql
```

### 3. Run Agent
```bash
python agent.py
```

## 📋 Setup Wizard

Saat pertama kali menjalankan `agent.py`, kamu akan diminta untuk:

1. **Supabase Credentials**
   - Project URL
   - Anon Key

2. **Agent Configuration**
   - Nama agent kamu (contoh: "Rover", "Noelle", "Raken")

3. **Room Selection**
   - **Create New Room**: Generate room baru dengan token unik
   - **Join Existing Room**: Bergabung ke room lain pakai token

4. **9router Configuration**
   - Endpoint URL (default: `http://localhost:20128/v1/chat/completions`)
   - API Key (optional)
   - Model ID (default: `openhermes`)

## 🏗️ Database Schema

### Tabel `rooms`
- `id` (UUID) - Primary Key
- `token` (Text, unique) - Secret key untuk otentikasi agent
- `created_at` (Timestamp) - Waktu pembuatan room

### Tabel `messages`
- `id` (BigInt) - Primary Key
- `room_id` (FK ke rooms.id)
- `sender` (Text) - Nama agent pengirim
- `content` (Text) - Isi pesan
- `timestamp` (Timestamp) - Waktu pesan dikirim

**Note:** Enable Supabase Realtime di tabel `messages` supaya agent dapat mendengarkan pesan real-time!

## 💬 Cara Kerja

1. **Room Creation/Joining**: Agent membuat atau bergabung ke room tertentu
2. **Message Polling**: Agent secara berkala mengecek pesan baru di room
3. **Turn-based Response**: Jika pesan terakhir bukan dari agent itu, maka agent akan merespons
4. **AI Integration**: Respons di-generate via 9router (LM Studio, Ollama, atau API)
5. **Consensus Detection**: Diskusi selesai saat ada `[SELESAI]` di pesan

## 🔧 Troubleshooting

### Error: "9router Error 405"
- Pastikan 9router/LM Studio/Ollama sudah berjalan di port yang ditentukan
- Cek endpoint URL sudah benar

### Error: "Room token tidak ditemukan"
- Pastikan token room sudah benar (copy dari room creator)
- Verifikasi di Supabase bahwa row `rooms` sudah ada

### Agent tidak merespons
- Pastikan pesan terakhir bukan dari agent itu sendiri
- Cek koneksi ke Supabase & 9router
- Pastikan `messages` table sudah enable Realtime

## 📝 Testing dengan 2 Agent

```bash
# Terminal 1: Create new room, jalankan Agent 1
python agent.py
# Pilih: Buat room baru
# Nama: Noelle
# Copy room token yang di-generate

# Terminal 2: Join ke room itu, jalankan Agent 2
python agent.py
# Pilih: Join room yang sudah ada
# Paste: room token dari Terminal 1
# Nama: Raken
```

Lalu input topik pembuka di salah satu terminal, dan lihat mereka auto-diskusi! 🎉

## 🤖 Agent Behavior

- Agent hanya merespons jika pesan terakhir **bukan** dari dirinya
- Atau jika ada mention khusus: `@AgentName` atau `AgentName:`
- Diskusi selesai otomatis saat ada `[SELESAI]` di pesan

## 📦 Dependencies

- `supabase>=2.0.0` - Supabase client
- `requests>=2.31.0` - HTTP client untuk 9router
- `rich>=13.0.0` - Terminal UI formatting

---

Made for **USRC Multi-Agent Brainstorming** • Maintained by Chelo (Greeezzz)
