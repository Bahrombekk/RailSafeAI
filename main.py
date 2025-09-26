"""
RailSafeAI - Asosiy ishga tushirish fayli
Ko'cha kuzatuvi tizimi
"""

import cv2
import numpy as np
import time
from collections import defaultdict

# Modullarni import qilish
from config.settings import *
from config.paths import Paths
from modules.detector import VehicleDetector
from modules.tracker import VehicleTracker
from modules.polygon_utils import PolygonManager
from modules.speed_estimator import SpeedEstimator
from modules.recorder import VideoRecorder
from modules.ocr_reader import OCRReader

class RailSafeAI:
    """Asosiy RailSafeAI tizimi"""
    
    def __init__(self):
        print("RailSafeAI tizimi ishga tushmoqda...")
        
        # Modullarni ishga tushirish
        self.detector = VehicleDetector(YOLO_MODEL_PATH)
        self.tracker = VehicleTracker()
        self.polygon_manager = PolygonManager()
        self.speed_estimator = SpeedEstimator()
        self.recorder = VideoRecorder()
        self.ocr_reader = OCRReader()
        
        # Kameralar uchun VideoCapture obyektlari
        self.cameras = {}
        self.camera_configs = {}
        
        # Asosiy holatlar
        self.running = True
        self.frame_count = defaultdict(int)
        
        # Kameralarni ishga tushirish
        self._initialize_cameras()
        
        print("RailSafeAI tizimi tayyor!")
        self._print_controls()
    
    def _initialize_cameras(self):
        """Kameralarni ishga tushirish"""
        for cam_config in CAMERAS:
            if not cam_config['enabled']:
                continue
            
            camera_id = cam_config['id']
            source = cam_config['source']
            
            try:
                cap = cv2.VideoCapture(source)
                if cap.isOpened():
                    self.cameras[camera_id] = cap
                    self.camera_configs[camera_id] = cam_config
                    
                    # Polygon yuklash
                    if self.polygon_manager.load_polygon(camera_id, cam_config['polygon_file']):
                        print(f"✓ Kamera {camera_id} muvaffaqiyatli ishga tushdi")
                    else:
                        print(f"✗ Kamera {camera_id} uchun polygon yuklanmadi")
                        cap.release()
                        continue
                else:
                    print(f"✗ Kamera {camera_id} ochilmadi: {source}")
                    
            except Exception as e:
                print(f"✗ Kamera {camera_id} xatosi: {e}")
    
    def _print_controls(self):
        """Boshqaruv tugmalarini ko'rsatish"""
        print("\n" + "="*50)
        print("BOSHQARUV TUGMALARI:")
        print(f"  {CONTROLS['start_detection'].upper()} - Avtomobil aniqlashni BOSHLASH")
        print(f"  {CONTROLS['stop_detection'].upper()} - Avtomobil aniqlashni TO'XTATISH")
        print(f"  {CONTROLS['start_recording'].upper()} - Video yozishni BOSHLASH")
        print(f"  {CONTROLS['stop_recording'].upper()} - Video yozishni TO'XTATISH")
        print(f"  {CONTROLS['exit'].upper()} - Dasturdan CHIQISH")
        print("="*50 + "\n")
    
    def process_camera_frame(self, camera_id, frame):
        """Bitta kamera kadrisini qayta ishlash"""
        if frame is None:
            return None
        
        cam_config = self.camera_configs[camera_id]
        current_time = self.frame_count[camera_id] / VIDEO_SETTINGS['fps']
        
        # Polygon chizish
        frame = self.polygon_manager.draw_polygon(frame, camera_id)
        
        # Avtomobillarni aniqlash (agar yoqilgan bo'lsa)
        if cam_config['detection_active'] and self.detector.is_detection_enabled():
            results = self.detector.detect_and_track(frame)
            vehicles = self.detector.get_vehicle_data(results)
            
            # Debug: Print vehicles to inspect track_id structure
            #print(f"Camera {camera_id} vehicles: {vehicles}")
            
            # Har bir avtomobil uchun
            active_ids = []
            for vehicle in vehicles:
                # Extract track_id with robust error handling
                if 'track_id' not in vehicle:
                    print(f"Warning: Vehicle missing track_id: {vehicle}")
                    continue
                
                track_id = vehicle['track_id']
                # Handle case where track_id is a dictionary
                if isinstance(track_id, dict):
                    if 'id' in track_id:
                        track_id = track_id['id']
                    else:
                        print(f"Error: track_id is a dict without 'id' key: {track_id}")
                        continue
                # Ensure track_id is hashable
                if not isinstance(track_id, (int, str)):
                    print(f"Error: track_id is not hashable: {track_id} (type: {type(track_id)})")
                    continue
                
                active_ids.append(track_id)
                center = vehicle['center']
                
                # Polygon ichida/tashqarisida ekanligini tekshirish
                is_inside = self.polygon_manager.point_in_polygon(camera_id, center)
                
                # Tracker da ma'lumotlarni yangilash
                self.tracker.update_vehicle(camera_id, vehicle, current_time, is_inside)
                
                # Tezlik hisoblash
                vehicle_info = self.tracker.get_vehicle_info(camera_id, track_id)
                speed_info = self.speed_estimator.get_speed_info(
                    vehicle_info, current_time, cam_config['polygon_length_meters']
                )
                
                # Video yozish (agar polygon ichida bo'lsa va yozish yoqilgan bo'lsa)
                if is_inside and cam_config['recording_active']:
                    frame_height, frame_width = frame.shape[:2]
                    
                    if self.recorder.start_vehicle_recording(
                        camera_id, track_id, frame_width, frame_height, VIDEO_SETTINGS['fps']
                    ):
                        self.recorder.write_vehicle_frame(camera_id, track_id, frame, vehicle_info)
                
                # OCR (agar yoqilgan bo'lsa)
                ocr_result = None
                if self.ocr_reader.is_enabled():
                    ocr_result = self.ocr_reader.process_vehicle_for_ocr(frame, vehicle)
                    if ocr_result:
                        frame = self.ocr_reader.draw_license_plate(frame, vehicle, ocr_result)
                
                # Ma'lumotlarni framega chizish
                frame = self.tracker.draw_vehicle_info(frame, camera_id, track_id, speed_info)
            
            # Aniqlanganlarni chizish
            frame = self.detector.draw_detections(frame, vehicles, self.tracker.vehicle_tracking, camera_id)
            
            # Eski avtomobillarni tozalash
            self.tracker.cleanup_old_vehicles(camera_id, current_time)
            self.recorder.cleanup_vehicle_recordings(camera_id, active_ids)
        
        # Holatni ko'rsatish
        self._draw_status(frame, camera_id)
        
        # Asosiy videoga yozish
        if cam_config['recording_active']:
            self.recorder.write_main_frame(camera_id, frame)
        
        return frame
    
    def _draw_status(self, frame, camera_id):
        """Holatni framega chizish"""
        cam_config = self.camera_configs[camera_id]
        y_pos = 30
        
        # Aniqlash holati
        detection_text = "ANIQLASH: ON" if cam_config['detection_active'] else "ANIQLASH: OFF"
        detection_color = TEXT_SETTINGS['colors']['detection_on'] if cam_config['detection_active'] else TEXT_SETTINGS['colors']['detection_off']
        cv2.putText(frame, detection_text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, detection_color, 2)
        y_pos += 25
        
        # Yozish holati
        recording_text = "YOZISH: ON" if cam_config['recording_active'] else "YOZISH: OFF"
        recording_color = TEXT_SETTINGS['colors']['recording_on'] if cam_config['recording_active'] else TEXT_SETTINGS['colors']['recording_off']
        cv2.putText(frame, recording_text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, recording_color, 2)
        y_pos += 25
        
        # Kamera ID
        cv2.putText(frame, f"KAMERA: {camera_id}", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Statistika
        stats = self.tracker.get_statistics(camera_id)
        stats_text = f"Jami: {stats['total_vehicles']} | Faol: {stats['active_in_polygon']}"
        cv2.putText(frame, stats_text, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
    
    def handle_key_press(self, key):
        """Tugma bosishni qayta ishlash"""
        key_char = chr(key).lower()
        
        if key_char == CONTROLS['exit']:
            self.running = False
            print("Dastur to'xtatilmoqda...")
        
        elif key_char == CONTROLS['start_detection']:
            # Barcha kameralar uchun aniqlashni yoqish
            for camera_id in self.camera_configs:
                self.camera_configs[camera_id]['detection_active'] = True
            self.detector.set_detection_enabled(True)
            print("✓ Barcha kameralar uchun ANIQLASH yoqildi")
        
        elif key_char == CONTROLS['stop_detection']:
            # Barcha kameralar uchun aniqlashni o'chirish
            for camera_id in self.camera_configs:
                self.camera_configs[camera_id]['detection_active'] = False
            self.detector.set_detection_enabled(False)
            print("✗ Barcha kameralar uchun ANIQLASH o'chirildi")
        
        elif key_char == CONTROLS['start_recording']:
            # Barcha kameralar uchun yozishni yoqish
            for camera_id in self.camera_configs:
                cam_config = self.camera_configs[camera_id]
                cam_config['recording_active'] = True
                
                # Asosiy video yozishni boshlash
                if camera_id in self.cameras:
                    cap = self.cameras[camera_id]
                    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS) or VIDEO_SETTINGS['fps']
                    
                    self.recorder.start_main_recording(camera_id, frame_width, frame_height, fps)
            
            self.recorder.set_recording_enabled(True)
            print("✓ Barcha kameralar uchun YOZISH yoqildi")
        
        elif key_char == CONTROLS['stop_recording']:
            # Barcha kameralar uchun yozishni o'chirish
            for camera_id in self.camera_configs:
                self.camera_configs[camera_id]['recording_active'] = False
                self.recorder.stop_main_recording(camera_id)
            
            self.recorder.set_recording_enabled(False)
            print("✗ Barcha kameralar uchun YOZISH o'chirildi")
    
    def run(self):
        """Asosiy ishga tushirish sikli"""
        if not self.cameras:
            print("Hech qanday kamera topilmadi. Dastur to'xtatildi.")
            return
        
        print("Tizim ishga tushdi! Video oynalarini yoping...")
        
        while self.running:
            frames_to_show = {}
            
            # Har bir kamera uchun
            for camera_id, cap in self.cameras.items():
                success, frame = cap.read()
                if not success:
                    print(f"Kamera {camera_id} da kadr o'qilmadi")
                    continue
                
                # Kadrni qayta ishlash
                processed_frame = self.process_camera_frame(camera_id, frame)
                if processed_frame is not None:
                    # Ekranda ko'rsatish uchun kichraytirish
                    if VIDEO_SETTINGS['resize_display']:
                        h, w = processed_frame.shape[:2]
                        new_w = int(w * VIDEO_SETTINGS['resize_factor'])
                        new_h = int(h * VIDEO_SETTINGS['resize_factor'])
                        processed_frame = cv2.resize(processed_frame, (new_w, new_h))
                    
                    frames_to_show[camera_id] = processed_frame
                
                self.frame_count[camera_id] += 1
            
            # Oynalarda ko'rsatish
            for camera_id, frame in frames_to_show.items():
                window_name = f"RailSafeAI - Kamera {camera_id}"
                cv2.imshow(window_name, frame)
            
            # Tugmalarni tekshirish
            key = cv2.waitKey(1) & 0xFF
            if key != 255:  # 255 = hech qanday tugma bosilmagan
                self.handle_key_press(key)
        
        # Tozalash
        self.cleanup()
    
    def cleanup(self):
        """Resurslarni tozalash"""
        print("Resurslar tozalanmoqda...")
        
        # Barcha yozishni to'xtatish
        self.recorder.stop_all_recordings()
        
        # Kameralarni yopish
        for cap in self.cameras.values():
            cap.release()
        
        # Oynalarni yopish
        cv2.destroyAllWindows()
        
        # Statistikani ko'rsatish
        self.print_final_statistics()
        
        print("RailSafeAI to'xtatildi!")
    
    def print_final_statistics(self):
        """Yakuniy statistikani chop etish"""
        print("\n" + "="*60)
        print("YAKUNIY STATISTIKA")
        print("="*60)
        
        for camera_id in self.camera_configs:
            print(f"\nKamera {camera_id}:")
            stats = self.tracker.get_statistics(camera_id)
            
            if stats['vehicles_data']:
                print(f"  Jami avtomobillar: {stats['completed_vehicles']}")
                print("  ID | Turi    | Vaqt(s) | Tezlik(km/h)")
                print("  " + "-"*40)
                
                for vehicle_data in stats['vehicles_data']:
                    print(f"  {vehicle_data['id']:2d} | {vehicle_data['class']:8s} | "
                          f"{vehicle_data['time']:6.2f}s | {vehicle_data['speed']:8.1f}km/h")
            else:
                print("  Hech qanday avtomobil aniqlanmadi")
        
        print("="*60)


def main():
    """Asosiy funktsiya"""
    try:
        # Papkalarni yaratish
        Paths.create_directories()
        
        # RailSafeAI tizimini ishga tushirish
        system = RailSafeAI()
        system.run()
        
    except KeyboardInterrupt:
        print("\nDastur foydalanuvchi tomonidan to'xtatildi")
    except Exception as e:
        print(f"Xato yuz berdi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()