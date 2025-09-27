import cv2
import numpy as np
import time
import threading
from collections import defaultdict
from queue import Queue

# Modullarni import qilish
from config.settings import *
from config.paths import Paths
from modules.detector import VehicleDetector
from modules.tracker import VehicleTracker
from modules.polygon_utils import PolygonManager
from modules.speed_estimator import SpeedEstimator
from modules.recorder import VideoRecorder
from modules.ocr_reader import OCRReader

class CameraProcessor:
    """Bitta kamera uchun alohida processor"""
    
    def __init__(self, camera_id, cam_config, shared_components):
        self.camera_id = camera_id
        self.cam_config = cam_config
        self.running = False
        
        # Har bir kamera uchun alohida YOLO detector
        self.detector = VehicleDetector(YOLO_MODEL_PATH)
        
        # Shared components
        self.tracker = shared_components['tracker']
        self.polygon_manager = shared_components['polygon_manager']
        self.speed_estimator = shared_components['speed_estimator']
        self.recorder = shared_components['recorder']
        self.ocr_reader = shared_components['ocr_reader']
        
        # Kamera
        self.cap = None
        self.frame_count = 0
        
        # Thread-safe frame sharing
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # Recording tracking
        self._vehicle_recording_started = set()
        
        # FPS hisoblash uchun
        self.fps = 0.0
        self.last_frame_time = None
    
    def initialize_camera(self):
        """Kamerani ishga tushirish"""
        try:
            self.cap = cv2.VideoCapture(self.cam_config['source'])
            if self.cap.isOpened():
                # Polygon yuklash
                if self.polygon_manager.load_polygon(self.camera_id, self.cam_config['polygon_file']):
                    print(f"✓ Kamera {self.camera_id} muvaffaqiyatli ishga tushdi")
                    return True
                else:
                    print(f"✗ Kamera {self.camera_id} uchun polygon yuklanmadi")
                    self.cap.release()
                    return False
            else:
                print(f"✗ Kamera {self.camera_id} ochilmadi: {self.cam_config['source']}")
                return False
        except Exception as e:
            print(f"✗ Kamera {self.camera_id} xatosi: {e}")
            return False
    
    def process_frame(self, frame):
        """Kadrni qayta ishlash"""
        # FPS hisoblash uchun vaqtni o‘lchash
        start_time = time.time()
        
        current_time = self.frame_count / VIDEO_SETTINGS['fps']
        
        # Polygon chizish
        frame = self.polygon_manager.draw_polygon(frame, self.camera_id)
        
        # Avtomobillarni aniqlash (agar yoqilgan bo'lsa)
        if self.cam_config['detection_active'] and self.detector.is_detection_enabled():
            results = self.detector.detect_and_track(frame)
            vehicles = self.detector.get_vehicle_data(results)
            
            # Har bir avtomobil uchun
            active_ids = []
            for vehicle in vehicles:
                track_id = vehicle['track_id']
                
                # Track ID ni tekshirish
                if isinstance(track_id, dict):
                    print(f"Warning: track_id is dict: {track_id}")
                    continue
                if not isinstance(track_id, (int, str)):
                    print(f"Warning: Invalid track_id type: {type(track_id)}, value: {track_id}")
                    continue
                
                active_ids.append(track_id)
                center = vehicle['center']
                
                # Polygon ichida/tashqarisida ekanligini tekshirish
                is_inside = self.polygon_manager.point_in_polygon(self.camera_id, center)
                
                # Tracker da ma'lumotlarni yangilash
                self.tracker.update_vehicle(self.camera_id, vehicle, current_time, is_inside)
                
                # Tezlik hisoblash
                vehicle_info = self.tracker.get_vehicle_info(self.camera_id, track_id)
                speed_info = self.speed_estimator.get_speed_info(
                    vehicle_info, current_time, self.cam_config['polygon_length_meters']
                )
                
                # Video yozish
                if is_inside and self.cam_config['recording_active']:
                    frame_height, frame_width = frame.shape[:2]
                    
                    recording_key = f"{self.camera_id}_{track_id}"
                    if recording_key not in self._vehicle_recording_started:
                        if self.recorder.start_vehicle_recording(
                            self.camera_id, track_id, frame_width, frame_height, VIDEO_SETTINGS['fps']
                        ):
                            self._vehicle_recording_started.add(recording_key)
                    
                    # Video kadr yozish
                    self.recorder.write_vehicle_frame(self.camera_id, track_id, frame, vehicle_info)
                
                # OCR
                ocr_result = None
                if self.ocr_reader.is_enabled():
                    ocr_result = self.ocr_reader.process_vehicle_for_ocr(frame, vehicle)
                    if ocr_result:
                        frame = self.ocr_reader.draw_license_plate(frame, vehicle, ocr_result)
                
                # Ma'lumotlarni framega chizish
                frame = self.tracker.draw_vehicle_info(frame, self.camera_id, track_id, speed_info)
            
            # Aniqlanganlarni chizish
            frame = self.detector.draw_detections(frame, vehicles, self.tracker.vehicle_tracking, self.camera_id)
            
            # Eski avtomobillarni tozalash
            self.tracker.cleanup_old_vehicles(self.camera_id, current_time)
            self.recorder.cleanup_vehicle_recordings(self.camera_id, active_ids)
        
        # Status chizish
        self._draw_status(frame)
        
        # Asosiy videoga yozish
        if self.cam_config['recording_active']:
            self.recorder.write_main_frame(self.camera_id, frame)
        
        # FPS ni hisoblash
        end_time = time.time()
        frame_time = end_time - start_time
        if frame_time > 0:
            self.fps = 1.0 / frame_time
        else:
            self.fps = 0.0
        
        return frame
    
    def _draw_status(self, frame):
        """Holatni framega chizish"""
        y_pos = 30
        
        # Aniqlash holati
        detection_text = "ANIQLASH: ON" if self.cam_config['detection_active'] else "ANIQLASH: OFF"
        detection_color = TEXT_SETTINGS['colors']['detection_on'] if self.cam_config['detection_active'] else TEXT_SETTINGS['colors']['detection_off']
        cv2.putText(frame, detection_text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, detection_color, 2)
        y_pos += 25
        
        # Yozish holati
        recording_text = "YOZISH: ON" if self.cam_config['recording_active'] else "YOZISH: OFF"
        recording_color = TEXT_SETTINGS['colors']['recording_on'] if self.cam_config['recording_active'] else TEXT_SETTINGS['colors']['recording_off']
        cv2.putText(frame, recording_text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, recording_color, 2)
        y_pos += 25
        
        # Kamera ID
        cv2.putText(frame, f"KAMERA: {self.camera_id}", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_pos += 25
        
        # FPS ko‘rsatish
        fps_text = f"FPS: {self.fps:.1f}"
        cv2.putText(frame, fps_text, (10, y_pos+50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 1)
        
        # Statistika
        stats = self.tracker.get_statistics(self.camera_id)
        stats_text = f"Jami: {stats['total_vehicles']} | Faol: {stats['active_in_polygon']}"
        cv2.putText(frame, stats_text, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
    
    def run_processing(self):
        """Alohida thread da kamera ishlov berish"""
        if not self.initialize_camera():
            return
        
        self.running = True
        print(f"Kamera {self.camera_id} processing thread boshlandi")
        
        while self.running:
            try:
                success, frame = self.cap.read()
                if not success:
                    print(f"Kamera {self.camera_id} da kadr o'qilmadi")
                    break
                
                # Kadrni qayta ishlash
                processed_frame = self.process_frame(frame)
                
                # Ekranda ko'rsatish uchun kichraytirish
                if VIDEO_SETTINGS['resize_display']:
                    h, w = processed_frame.shape[:2]
                    new_w = int(w * VIDEO_SETTINGS['resize_factor'])
                    new_h = int(h * VIDEO_SETTINGS['resize_factor'])
                    processed_frame = cv2.resize(processed_frame, (new_w, new_h))
                
                # Thread-safe frame saqlash
                with self.frame_lock:
                    self.current_frame = processed_frame.copy()
                
                self.frame_count += 1
                
                # FPS limit (CPU yukini kamaytirish uchun)
                time.sleep(1/30)  # ~30 FPS
                
            except Exception as e:
                print(f"Kamera {self.camera_id} processing xatosi: {e}")
                break
        
        self.cleanup()
    
    def get_current_frame(self):
        """Joriy kadrni thread-safe olish"""
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None
    
    def stop(self):
        """Processing ni to'xtatish"""
        self.running = False
    
    def cleanup(self):
        """Resurslarni tozalash"""
        if self.cap:
            self.cap.release()
        print(f"Kamera {self.camera_id} tozalandi")

class RailSafeAI:
    """Asosiy RailSafeAI tizimi - ko'p thread li"""
    
    def __init__(self):
        print("RailSafeAI tizimi ishga tushmoqda...")
        
        # Shared components
        self.tracker = VehicleTracker()
        self.polygon_manager = PolygonManager()
        self.speed_estimator = SpeedEstimator()
        self.recorder = VideoRecorder()
        self.ocr_reader = OCRReader()
        
        shared_components = {
            'tracker': self.tracker,
            'polygon_manager': self.polygon_manager,
            'speed_estimator': self.speed_estimator,
            'recorder': self.recorder,
            'ocr_reader': self.ocr_reader
        }
        
        # Har bir kamera uchun alohida processor
        self.camera_processors = {}
        self.camera_threads = {}
        
        # Asosiy holatlar
        self.running = True
        
        # Kameralarni ishga tushirish
        self._initialize_cameras(shared_components)
        
        print("RailSafeAI tizimi tayyor!")
        self._print_controls()
    
    def _initialize_cameras(self, shared_components):
        """Kameralarni ishga tushirish"""
        for cam_config in CAMERAS:
            if not cam_config['enabled']:
                continue
            
            camera_id = cam_config['id']
            processor = CameraProcessor(camera_id, cam_config, shared_components)
            self.camera_processors[camera_id] = processor
    
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
    
    def handle_key_press(self, key):
        """Tugma bosishni qayta ishlash"""
        key_char = chr(key).lower()
        
        if key_char == CONTROLS['exit']:
            self.running = False
            print("Dastur to'xtatilmoqda...")
        
        elif key_char == CONTROLS['start_detection']:
            # Barcha kameralar uchun aniqlashni yoqish
            for processor in self.camera_processors.values():
                processor.cam_config['detection_active'] = True
                processor.detector.set_detection_enabled(True)
            print("✓ Barcha kameralar uchun ANIQLASH yoqildi")
        
        elif key_char == CONTROLS['stop_detection']:
            # Barcha kameralar uchun aniqlashni o'chirish
            for processor in self.camera_processors.values():
                processor.cam_config['detection_active'] = False
                processor.detector.set_detection_enabled(False)
            print("✗ Barcha kameralar uchun ANIQLASH o'chirildi")
        
        elif key_char == CONTROLS['start_recording']:
            # Barcha kameralar uchun yozishni yoqish
            for processor in self.camera_processors.values():
                processor.cam_config['recording_active'] = True
                # Asosiy video yozishni boshlash
                if processor.cap and processor.cap.isOpened():
                    frame_width = int(processor.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    frame_height = int(processor.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = processor.cap.get(cv2.CAP_PROP_FPS) or VIDEO_SETTINGS['fps']
                    self.recorder.start_main_recording(processor.camera_id, frame_width, frame_height, fps)
            
            self.recorder.set_recording_enabled(True)
            print("✓ Barcha kameralar uchun YOZISH yoqildi")
        
        elif key_char == CONTROLS['stop_recording']:
            # Barcha kameralar uchun yozishni o'chirish
            for processor in self.camera_processors.values():
                processor.cam_config['recording_active'] = False
                self.recorder.stop_main_recording(processor.camera_id)
            
            self.recorder.set_recording_enabled(False)
            print("✗ Barcha kameralar uchun YOZISH o'chirildi")
    
    def run(self):
        """Asosiy ishga tushirish sikli"""
        if not self.camera_processors:
            print("Hech qanday kamera topilmadi. Dastur to'xtatildi.")
            return
        
        print("Tizim ishga tushdi! Video oynalarini yoping...")
        
        # Har bir kamera uchun alohida thread boshlash
        for camera_id, processor in self.camera_processors.items():
            thread = threading.Thread(target=processor.run_processing, daemon=True)
            thread.start()
            self.camera_threads[camera_id] = thread
        
        # UI thread - oynalarni ko'rsatish
        self._run_display_loop()
    
    def _run_display_loop(self):
        """Display loop - asosiy thread"""
        window_positions = {}
        x_offset = 0
        
        while self.running:
            # Har bir kameradan frame olish
            for camera_id, processor in self.camera_processors.items():
                frame = processor.get_current_frame()
                if frame is not None:
                    window_name = f"RailSafeAI - Kamera {camera_id}"
                    
                    # Oynani yaratish (agar mavjud bo'lmasa)
                    if camera_id not in window_positions:
                        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                        cv2.moveWindow(window_name, x_offset, 50)
                        window_positions[camera_id] = x_offset
                        x_offset += int(frame.shape[1] * 1.1)
                    
                    cv2.imshow(window_name, frame)
            
            # Tugmalarni tekshirish
            key = cv2.waitKey(1) & 0xFF
            if key != 255:
                self.handle_key_press(key)
            
            # CPU yukini kamaytirish
            time.sleep(0.01)
        
        # Tozalash
        self.cleanup()
    
    def cleanup(self):
        """Resurslarni tozalash"""
        print("Resurslar tozalanmoqda...")
        
        # Barcha processor threadlarini to'xtatish
        for processor in self.camera_processors.values():
            processor.stop()
        
        # Thread larni kutish
        for thread in self.camera_threads.values():
            thread.join(timeout=2.0)
        
        # Barcha yozishni to'xtatish
        self.recorder.stop_all_recordings()
        
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
        
        for camera_id in self.camera_processors.keys():
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