"""
RailSafeAI - OCR raqam o'qish moduli (hozircha o'chirilgan)
"""
from config.settings import OCR_ENABLED
import cv2

class OCRReader:
    """Avtomobil raqamlarini o'qish uchun klass"""
    
    def __init__(self):
        self.enabled = OCR_ENABLED
        self.ocr_engine = None
        
        if self.enabled:
            self._initialize_ocr()
    
    def _initialize_ocr(self):
        """OCR dvigatelni ishga tushirish"""
        try:
            # Bu yerda OCR kutubxonasini yuklash kerak (masalan, EasyOCR, PaddleOCR)
            # import easyocr
            # self.ocr_engine = easyocr.Reader(['en', 'uz'])
            print("OCR ENGINE ISHGA TUSHIRILDI (simulyatsiya)")
            pass
        except ImportError:
            print("OCR kutubxonasi o'rnatilmagan. OCR o'chirildi.")
            self.enabled = False
        except Exception as e:
            print(f"OCR ishga tushirishda xato: {e}")
            self.enabled = False
    
    def is_enabled(self):
        """OCR yoqilganligini tekshirish"""
        return self.enabled
    
    def set_enabled(self, enabled):
        """OCR ni yoqish/o'chirish"""
        self.enabled = enabled
        if enabled and self.ocr_engine is None:
            self._initialize_ocr()
        
        status = "YOQILDI" if enabled else "O'CHIRILDI"
        print(f"OCR raqam o'qish: {status}")
    
    def read_license_plate(self, frame, bbox):
        """Avtomobil raqamini o'qish"""
        if not self.enabled or self.ocr_engine is None:
            return None
        
        try:
            # Avtomobil hududini kesib olish
            x1, y1, x2, y2 = bbox
            vehicle_crop = frame[y1:y2, x1:x2]
            
            # Raqam maydoni topish va o'qish
            # Bu yerda murakkab algoritmlar bo'lishi kerak
            
            # Hozircha simulyatsiya
            license_plate = f"01A123BC"  # Test raqami
            confidence = 0.85
            
            return {
                'text': license_plate,
                'confidence': confidence,
                'bbox': None  # Raqam joylashuvi
            }
            
        except Exception as e:
            print(f"OCR da xato: {e}")
            return None
    
    def process_vehicle_for_ocr(self, frame, vehicle_info):
        """Avtomobil uchun OCR ishlov berish"""
        if not self.enabled:
            return None
        
        bbox = vehicle_info.get('bbox')
        if bbox is None:
            return None
        
        # Raqamni o'qish
        plate_info = self.read_license_plate(frame, bbox)
        
        if plate_info and plate_info['confidence'] > 0.7:
            return {
                'license_plate': plate_info['text'],
                'confidence': plate_info['confidence'],
                'timestamp': None  # Vaqt belgilash
            }
        
        return None
    
    def draw_license_plate(self, frame, vehicle_info, ocr_result):
        """Raqamni framega chizish"""
        if not ocr_result or not vehicle_info['bbox']:
            return frame
        
        x1, y1, x2, y2 = vehicle_info['bbox']
        
        # Raqamni ko'rsatish
        plate_text = f"Raqam: {ocr_result['license_plate']}"
        confidence_text = f"Ishonch: {ocr_result['confidence']:.2f}"
        
        # Matn joylashuvi
        text_y = y2 + 20
        
        cv2.putText(frame, plate_text, (x1, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        
        cv2.putText(frame, confidence_text, (x1, text_y + 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        return frame