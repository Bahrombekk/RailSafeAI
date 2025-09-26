# RailSafeAI - Ko'cha Kuzatuvi Tizimi

Professional ko'cha kuzatuvi tizimi avtomobillarni aniqlash, kuzatish va tezligini o'lchash uchun.

## ✨ Xususiyatlari

- 🚗 **Avtomobil aniqlash**: YOLO modelini qo'llash orqali
- 🎯 **Polygon zonasi**: Muayyan hudud ichidagi avtomobillarni kuzatish  
- ⚡ **Tezlik o'lchash**: Poligon ichidagi vaqt bo'yicha hisoblash
- 📹 **Video yozish**: Har bir avtomobil uchun alohida videolar
- 📸 **Rasm saqlash**: Avtomobil rasmlari
- 📊 **Statistika**: Detallı hisobotlar
- 🎛️ **Modullar**: OCR, tezlik, aniqlash - alohida yoqish/o'chirish
- 📷 **Ko'p kamera**: Bir necha kamerani bir vaqtda boshqarish

## 📁 Loyiha tuzilishi

```
RailSafeAI/
├── config/                     # Sozlamalar
│   ├── settings.py             # Asosiy konfiguratsiya
│   └── paths.py                # Fayl yo'llari
│
├── data/                       # Ma'lumotlar
│   ├── videos/                 # Kiruvchi videolar
│   ├── polygons/               # Polygon JSON fayllari  
│   └── outputs/                # Natijalar
│       ├── vehicle_videos/     # Avtomobil videolari
│       └── vehicle_images/     # Avtomobil rasmlari
│
├── models/                     # YOLO model fayllari
│   └── best.pt
│
├── modules/                    # Asosiy modullar
│   ├── detector.py             # YOLO obyekt aniqlash
│   ├── tracker.py              # Avtomobil kuzatish
│   ├── polygon_utils.py        # Polygon funksiyalari
│   ├── speed_estimator.py      # Tezlik hisoblash
│   ├── recorder.py             # Video/rasm yozish
│   └── ocr_reader.py           # Raqam o'qish (OCR)
│
├── main.py                     # Asosiy ishga tushirish
├── requirements.txt            # Python kutubxonalari
└── README.md                   # Bu fayl
```

## 🚀 O'rnatish

1. **Repositoriyni klonlash**:
```bash
git clone <repository-url>
cd RailSafeAI
```

2. **Virtual muhit yaratish**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\Scripts\activate     # Windows
```

3. **Kutubxonalarni o'rnatish**:
```bash
pip install -r requirements.txt
```

4. **YOLO modelini joylashtirish**:
   - `models/best.pt` faylini joylashtiring

5. **Konfiguratsiyani sozlash**:
   - `config/settings.py` faylida sozlamalarni o'zgartiring

## ⚙️ Konfiguratsiya

`config/settings.py` faylida asosiy sozlamalar:

```python
# Modullarni yoqish/o'chirish
OCR_ENABLED = False                    # OCR (raqam o'qish)
SPEED_ESTIMATION_ENABLED = True        # Tezlik hisoblash  
AUTO_DETECTION_ENABLED = False         # Avtomatik aniqlash
RECORDING_ENABLED = True               # Video yozish

# Tugmalar
CONTROLS = {
    'start_detection': 'f',            # Aniqlashni boshlash
    'stop_detection': 'g',             # Aniqlashni to'xtatish
    'start_recording': 'r',            # Video yozish
    'stop_recording': 't',             # Video to'xtatish
    'exit': 'q'                        # Chiqish
}

# Kameralar
CAMERAS = [
    {
        'id': 'cam1',
        'source': 'video/test.mp4',    # Video fayl yoki kamera indeksi
        'polygon_file': 'polygon_cam1.json',
        'polygon_length_meters': 8.0,
        'enabled': True
    }
]
```

## 🎮 Foydalanish

1. **Dasturni ishga tushirish**:
```bash
python main.py
```

2. **Boshqaruv tugmalari**:
   - `F` - Avtomobil aniqlashni boshlash
   - `G` - Avtomobil aniqlashni to'xtatish
   - `R` - Video yozishni boshlash
   - `T` - Video yozishni to'xtatish
   - `Q` - Dasturdan chiqish

3. **Natijalar**:
   - Avtomobil videolari: `data/outputs/vehicle_videos/`
   - Avtomobil rasmlari: `data/outputs/vehicle_images/`

## 📊 Modullar

### 🎯 Detector (detector.py)
- YOLO model orqali avtomobil aniqlash
- F/G tugmalar orqali yoqish/o'chirish
- `AUTO_DETECTION_ENABLED` sozlamasi

### 🏃 Tracker (tracker.py) 
- Avtomobillarni ID bilan kuzatish
- Polygon kirish/chiqish vaqtlarini hisobga olish
- Statistika yig'ish

### ⚡ Speed Estimator (speed_estimator.py)
- Polygon uzunligiga asosan tezlik hisoblash
- `SPEED_ESTIMATION_ENABLED` orqali boshqarish
- Joriy va o'rtacha tezlik

### 📹 Recorder (recorder.py)
- Har bir avtomobil uchun alohida video
- R/T tugmalar orqali boshqarish
- Asosiy monitoring video

### 🔤 OCR Reader (ocr_reader.py)
- Avtomobil raqamlarini o'qish (hozircha o'chirilgan)
- `OCR_ENABLED` orqali yoqish
- EasyOCR/PaddleOCR qo'llab-quvvatlaydi

### 📐 Polygon Utils (polygon_utils.py)
- JSON formatdagi poligon fayllari
- Nuqta ichida/tashqarisida tekshirish
- Visualizatsiya

## 🎛️ Ko'p Kamera Boshqaruvi

Bir necha kameralik tizim:

```python
CAMERAS = [
    {
        'id': 'cam1',
        'source': 'video1.mp4',
        'polygon_file': 'polygon_cam1.json',
        'polygon_length_meters': 8.0,
        'enabled': True
    },
    {
        'id': 'cam2', 
        'source': 0,  # USB kamera
        'polygon_file': 'polygon_cam2.json',
        'polygon_length_meters': 12.0,
        'enabled': True
    }
]
```

Har bir kamera uchun:
- Alohida polygon fayli
- Mustaqil F/G/R/T boshqaruvi
- Alohida video va rasm fayllari

## 🔧 Muammolarni hal qilish

### Model yuklanmadi
```bash
# YOLO modelini tekshiring
ls models/best.pt
```

### Kamera ochilmadi
```bash
# Video fayl yo'lini tekshiring yoki kamera indeksini o'zgartiring
# config/settings.py da CAMERAS sozlamasi
```

### Polygon yuklanmadi  
```bash
# JSON fayl formatini tekshiring
# data/polygons/ papkasida polygon fayli borligini tasdiqlang
```

## 📈 Kengaytirishlar

- **Database integratsiyasi**: Natijalarni bazaga saqlash
- **Real-time API**: REST API orqali boshqarish  
- **Web interface**: Browser orqali monitoring
- **Alert tizimi**: Tezlik chegarasini oshirish holatida ogohlantirish
- **Analytics**: Detallı statistik hisobotlar

## 👨‍💻 Ishlab chiquvchi

Ko'cha xavfsizligi uchun professional monitoring tizimi.

**Maqsad**: Avtomobil harakatini kuzatish va tezlik nazorati orqali yo'l xavfsizligini ta'minlash.

## 📄 Litsenziya

MIT License - batafsil ma'lumot uchun LICENSE faylini ko'ring.