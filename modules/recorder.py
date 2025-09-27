"""
RailSafeAI - Video va rasm yozish moduli
"""
import cv2
import os
from datetime import datetime
from time import time
from config.settings import RECORDING_ENABLED, VIDEO_SETTINGS, SAVE_SETTINGS
from config.paths import Paths

class VideoRecorder:
    """Video va rasm yozish uchun klass"""
    
    def __init__(self):
        self.recording_enabled = RECORDING_ENABLED
        # Har bir kamera va avtomobil uchun video yozuvchi
        self.vehicle_recorders = {}  # {camera_id: {track_id: recorder_info}}
        self.main_recorders = {}     # {camera_id: main_recorder}
        
        # Papkalarni yaratish
        Paths.create_directories()
    
    def is_recording_enabled(self):
        """Video yozish yoqilganligini tekshirish"""
        return self.recording_enabled
    
    def set_recording_enabled(self, enabled):
        """Video yozishni yoqish/o'chirish"""
        self.recording_enabled = enabled
        status = "YOQILDI" if enabled else "O'CHIRILDI"
        print(f"Video yozish: {status}")
        
        if not enabled:
            # Barcha yozishni to'xtatish
            self.stop_all_recordings()
    
    def start_main_recording(self, camera_id, frame_width, frame_height, fps):
        """Asosiy video yozishni boshlash (barcha kadr)"""
        if not self.recording_enabled:
            return False
        
        if camera_id in self.main_recorders:
            return True  # Allaqachon yozilmoqda
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"main_{camera_id}_{timestamp}.avi"
        filepath = Paths.get_video_save_path(filename)
        
        try:
            fourcc = cv2.VideoWriter_fourcc(*VIDEO_SETTINGS['codec'])
            writer = cv2.VideoWriter(filepath, fourcc, fps, (frame_width, frame_height))
            
            if writer.isOpened():
                self.main_recorders[camera_id] = {
                    'writer': writer,
                    'filename': filename,
                    'start_time': time()
                }
                print(f"Kamera {camera_id}: Asosiy video yozish boshlandi - {filename}")
                return True
            else:
                print(f"Xato: Kamera {camera_id} uchun video yozuvchi ochilmadi")
                return False
                
        except Exception as e:
            print(f"Xato asosiy video yozishni boshlashda: {e}")
            return False
    
    def stop_main_recording(self, camera_id):
        """Asosiy video yozishni to'xtatish"""
        if camera_id in self.main_recorders:
            recorder_info = self.main_recorders[camera_id]
            recorder_info['writer'].release()
            duration = time() - recorder_info['start_time']
            print(f"Kamera {camera_id}: Asosiy video yozish tugadi - {recorder_info['filename']} ({duration:.1f}s)")
            del self.main_recorders[camera_id]
    
    def write_main_frame(self, camera_id, frame):
        """Asosiy videoga kadr yozish"""
        if camera_id in self.main_recorders:
            self.main_recorders[camera_id]['writer'].write(frame)
    
    def start_vehicle_recording(self, camera_id, track_id, frame_width, frame_height, fps):
        """Alohida avtomobil uchun video yozishni boshlash"""
        if not self.recording_enabled:
            return False
        
        if camera_id not in self.vehicle_recorders:
            self.vehicle_recorders[camera_id] = {}
        
        # Agar allaqachon yozish boshlangan bo'lsa, qaytarish
        if track_id in self.vehicle_recorders[camera_id]:
            return True  # Allaqachon yozilmoqda
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vehicle_{camera_id}_{track_id}_{timestamp}.avi"
        filepath = Paths.get_video_save_path(filename)
        
        try:
            fourcc = cv2.VideoWriter_fourcc(*VIDEO_SETTINGS['codec'])
            writer = cv2.VideoWriter(filepath, fourcc, fps, (frame_width, frame_height))
            
            if writer.isOpened():
                self.vehicle_recorders[camera_id][track_id] = {
                    'writer': writer,
                    'filename': filename,
                    'start_time': time(),
                    'frames_recorded': 0,
                    'image_saved': False
                }
                print(f"Avtomobil {track_id} (kamera {camera_id}) uchun video yozish boshlandi")
                return True
            else:
                print(f"Xato: Avtomobil {track_id} uchun video yozuvchi ochilmadi")
                return False
                
        except Exception as e:
            print(f"Xato avtomobil video yozishni boshlashda: {e}")
            return False
    
    def write_vehicle_frame(self, camera_id, track_id, frame, vehicle_info):
        """Avtomobil videosiga kadr yozish"""
        if (camera_id in self.vehicle_recorders and 
            track_id in self.vehicle_recorders[camera_id]):
            
            recorder_info = self.vehicle_recorders[camera_id][track_id]
            
            # Avtomobil atrofiga to'rtburchak chizish
            record_frame = frame.copy()
            if vehicle_info and vehicle_info['bbox']:
                x1, y1, x2, y2 = vehicle_info['bbox']
                cv2.rectangle(record_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                
                # Ma'lumot yozish
                info_text = f"ID:{track_id} {vehicle_info['class_name']}"
                cv2.putText(record_frame, info_text, (x1, y1-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            recorder_info['writer'].write(record_frame)
            recorder_info['frames_recorded'] += 1
            
            # Rasm saqlash (bir marta)
            if not recorder_info['image_saved'] and SAVE_SETTINGS['save_individual_images']:
                self.save_vehicle_image(camera_id, track_id, record_frame)
                recorder_info['image_saved'] = True
            
            # Vaqt tugashi bo'yicha to'xtatish
            duration = time() - recorder_info['start_time']
            if duration >= VIDEO_SETTINGS['individual_vehicle_recording_duration']:
                self.stop_vehicle_recording(camera_id, track_id)
    
    def stop_vehicle_recording(self, camera_id, track_id):
        """Avtomobil video yozishni to'xtatish"""
        if (camera_id in self.vehicle_recorders and 
            track_id in self.vehicle_recorders[camera_id]):
            
            recorder_info = self.vehicle_recorders[camera_id][track_id]
            recorder_info['writer'].release()
            duration = time() - recorder_info['start_time']
            
            print(f"Avtomobil {track_id} (kamera {camera_id}) video yozish tugadi - "
                  f"{recorder_info['filename']} ({duration:.1f}s, {recorder_info['frames_recorded']} kadr)")
            
            del self.vehicle_recorders[camera_id][track_id]
    
    def save_vehicle_image(self, camera_id, track_id, frame):
        """Avtomobil rasmini saqlash"""
        if not SAVE_SETTINGS['save_individual_images']:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vehicle_{camera_id}_{track_id}_{timestamp}.jpg"
        filepath = Paths.get_image_save_path(filename)
        
        try:
            cv2.imwrite(filepath, frame)
            print(f"Avtomobil {track_id} rasmi saqlandi: {filename}")
        except Exception as e:
            print(f"Xato rasm saqlashda: {e}")
    
    def stop_all_recordings(self):
        """Barcha video yozishni to'xtatish"""
        # Asosiy video yozishni to'xtatish
        for camera_id in list(self.main_recorders.keys()):
            self.stop_main_recording(camera_id)
        
        # Avtomobil videolarini to'xtatish
        for camera_id in list(self.vehicle_recorders.keys()):
            for track_id in list(self.vehicle_recorders[camera_id].keys()):
                self.stop_vehicle_recording(camera_id, track_id)
        
        print("Barcha video yozish to'xtatildi")
    
    def cleanup_vehicle_recordings(self, camera_id, active_track_ids):
        """Faol bo'lmagan avtomobil yozishlarini tozalash"""
        if camera_id not in self.vehicle_recorders:
            return
        
        to_remove = []
        for track_id in self.vehicle_recorders[camera_id].keys():
            if track_id not in active_track_ids:
                to_remove.append(track_id)
        
        for track_id in to_remove:
            self.stop_vehicle_recording(camera_id, track_id)
    
    def get_recording_status(self):
        """Yozish holatini olish"""
        status = {
            'enabled': self.recording_enabled,
            'main_recordings': len(self.main_recorders),
            'vehicle_recordings': sum(len(cams) for cams in self.vehicle_recorders.values())
        }
        return status