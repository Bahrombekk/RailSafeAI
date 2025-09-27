"""
RailSafeAI - YOLO obyekt aniqlash moduli
"""
from ultralytics import YOLO
from config.settings import AUTO_DETECTION_ENABLED, TARGET_CLASSES, CLASS_NAMES
from config.paths import Paths
import cv2

class VehicleDetector:
    """YOLO yordamida avtomobil aniqlash uchun klass"""
    
    def __init__(self, model_path):
        """Detektorni ishga tushirish"""
        try:
            full_model_path = Paths.get_model_path(model_path)
            self.model = YOLO(full_model_path)
            print(f"YOLO model yuklandi: {full_model_path}")
        except Exception as e:
            print(f"Xato: Model yuklanmadi - {e}")
            self.model = None
        
        self.detection_enabled = AUTO_DETECTION_ENABLED
        self.target_classes = TARGET_CLASSES
        
    def is_detection_enabled(self):
        """Aniqlash yoqilganligini tekshirish"""
        return self.detection_enabled
    
    def set_detection_enabled(self, enabled):
        """Aniqlashni yoqish/o'chirish"""
        self.detection_enabled = enabled
        status = "YOQILDI" if enabled else "O'CHIRILDI"
        print(f"Avtomobil aniqlash: {status}")
    
    def detect_and_track(self, frame):
        """Frameda avtomobillarni aniqlash va kuzatish"""
        if not self.detection_enabled or self.model is None:
            return None
        
        try:
            # YOLO model bilan aniqlash va kuzatish
            results = self.model.track(
                frame, 
                persist=True, 
                classes=self.target_classes,
                verbose=False  # Chop etishni kamaytirish
            )
            return results
        except Exception as e:
            print(f"Aniqlashda xato: {e}")
            return None
    
    def get_vehicle_data(self, results):
        """Aniqlangan avtomobillar ma'lumotlarini chiqarish"""
        vehicles = []
        
        if not results or results[0].boxes is None:
            return vehicles
        
        boxes = results[0].boxes
        
        for box in boxes:
            if hasattr(box, 'id') and box.id is not None:
                # Track ID ni to'g'ri chiqarish
                raw_track_id = box.id[0]
                
                # Agar tensor bo'lsa, CPU ga o'tkazib, int ga aylantirish
                if hasattr(raw_track_id, 'cpu'):
                    track_id = int(raw_track_id.cpu().numpy())
                elif hasattr(raw_track_id, 'item'):
                    track_id = int(raw_track_id.item())
                else:
                    track_id = int(raw_track_id)
                
                class_id = int(box.cls[0])
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0])
                
                # Markaziy nuqtani hisoblash
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                vehicle_data = {
                    'track_id': track_id,  # Endi bu int bo'ladi
                    'class_id': class_id,
                    'class_name': CLASS_NAMES.get(class_id, 'Unknown'),
                    'bbox': (int(x1), int(y1), int(x2), int(y2)),
                    'center': (center_x, center_y),
                    'confidence': confidence
                }
                
                vehicles.append(vehicle_data)
        
        return vehicles
    
    def draw_detections(self, frame, vehicles, vehicle_tracking, camera_id):
        """Aniqlangan avtomobillarni framega chizish"""
        for vehicle in vehicles:
            track_id = vehicle['track_id']
            x1, y1, x2, y2 = vehicle['bbox']
            class_name = vehicle['class_name']
            
            # Rang tanlash (polygon ichida/tashqarida)
            if track_id in vehicle_tracking[camera_id] and vehicle_tracking[camera_id][track_id]['in_polygon']:
                color = (0, 0, 255)  # Qizil - polygon ichida
                thickness = 3
            else:
                color = (255, 0, 0)  # Ko'k - polygon tashqarida
                thickness = 2
            
            # To'rtburchak chizish
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            
            # ID va klass nomini yozish
            label = f"ID:{track_id} {class_name}"
            cv2.putText(frame, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return frame