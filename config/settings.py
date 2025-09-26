"""
RailSafeAI - Konfiguratsiya fayli
Ko'cha kuzatuvi tizimi sozlamalari
"""

# ===== ASOSIY SOZLAMALAR =====
# OCR moduli (raqamlarni o'qish)
OCR_ENABLED = False  # True - yoqilgan, False - o'chirilgan

# Tezlik hisoblash moduli  
SPEED_ESTIMATION_ENABLED = True  # True - yoqilgan, False - o'chirilgan

# Avtomatik aniqlash (F tugmasi bosmaguncha aniqlash)
AUTO_DETECTION_ENABLED = True  # True - avtomatik, False - faqat F tugmasi orqali

# Video yozish funksiyasi
RECORDING_ENABLED = True  # True - yoqilgan, False - o'chirilgan

# ===== TUGMALAR SOZLAMALARI =====
CONTROLS = {
    'start_detection': 'f',     # Aniqlashni boshlash tugmasi
    'stop_detection': 'g',      # Aniqlashni to'xtatish tugmasi  
    'start_recording': 'r',     # Video yozishni boshlash
    'stop_recording': 't',      # Video yozishni to'xtatish
    'exit': 'q'                 # Chiqish tugmasi
}

# ===== KAMERA SOZLAMALARI =====
CAMERAS = [
    {
        'id': 'cam1',
        'source': '/home/bahrombek/Desktop/RailSafeAI/data/videos/4.mp4',  # Video fayl yo'li yoki kamera indeksi (0, 1, 2...)
        'polygon_file': '/home/bahrombek/Desktop/RailSafeAI/data/polygons/paligon1.json',
        'polygon_length_meters': 8.0,  # Polygon uzunligi (metrda)
        'enabled': True,
        'detection_active': True,  # Boshlang'ich holatda o'chirilgan
        'recording_active': True,
        'position': (0, 0)  # Ekranda ko'rsatish pozitsiyasi
    },
    # Qo'shimcha kameralar qo'shish mumkin:
    # {
    #     'id': 'cam2', 
    #     'source': "/home/bahrombek/Desktop/RailSafeAI/data/videos/video_2025-09-25_11-09-32.mp4",  # USB kamera
    #     'polygon_file': '/home/bahrombek/Desktop/RailSafeAI/data/polygons/paligon3.json',
    #     'polygon_length_meters': 12.0,
    #     'enabled': True,
    #     'detection_active': False,
    #     'recording_active': False,
    #     'position': (640, 0)
    # }
]

# ===== MODEL SOZLAMALARI =====
YOLO_MODEL_PATH = "/home/bahrombek/Desktop/RailSafeAI/models/best.pt"
TARGET_CLASSES = [0]  # 0 - avtomobil klassi

CLASS_NAMES = {
    0: 'Car'
}

# ===== VIDEO SOZLAMALARI =====
VIDEO_SETTINGS = {
    'codec': 'XVID',
    'fps': 30,
    'quality': 95,
    'individual_vehicle_recording_duration': 10.0,  # sekundda
    'resize_display': True,  # Ko'rsatish uchun kichraytirish
    'resize_factor': 0.5     # Kichraytirish koeffitsienti
}

# ===== SAQLASH SOZLAMALARI =====
SAVE_SETTINGS = {
    'output_dir': 'data/outputs',
    'video_dir': 'vehicle_videos', 
    'image_dir': 'vehicle_images',
    'main_video_filename': 'railsafe_monitoring.avi',
    'save_individual_images': True,
    'save_individual_videos': True
}

# ===== POLYGON SOZLAMALARI =====
POLYGON_SETTINGS = {
    'line_color': (0, 255, 0),      # Yashil rang
    'line_thickness': 2,
    'fill_alpha': 0.3               # Shaffoqlik
}

# ===== MATN SOZLAMALARI =====
TEXT_SETTINGS = {
    'font': 'FONT_HERSHEY_SIMPLEX',
    'font_scale': 0.6,
    'thickness': 2,
    'colors': {
        'inside_polygon': (0, 255, 255),    # Sariq
        'outside_polygon': (255, 255, 255), # Oq
        'recording_on': (0, 255, 0),        # Yashil
        'recording_off': (0, 0, 255),       # Qizil
        'detection_on': (255, 0, 255),      # Binafsha
        'detection_off': (128, 128, 128)    # Kulrang
    }
}

# ===== DEBUG SOZLAMALARI =====
DEBUG = {
    'print_vehicle_info': True,
    'show_fps': True,
    'show_polygon_info': True,
    'verbose_logging': False
}