"""
RailSafeAI - Avtomobil kuzatish moduli
"""
from collections import defaultdict
from config.settings import TEXT_SETTINGS
import cv2

class VehicleTracker:
    """Avtomobillarni kuzatish va ma'lumotlarni saqlash uchun klass"""
    
    def __init__(self):
        # Har bir kamera uchun avtomobil ma'lumotlari
        self.vehicle_tracking = defaultdict(lambda: defaultdict(lambda: {
            'start_time': None,
            'end_time': None,
            'in_polygon': False,
            'total_time': 0,
            'speed': 0,
            'current_speed': 0,
            'class_id': None,
            'class_name': None,
            'confidence': 0,
            'bbox': None,
            'center': None,
            'last_seen': 0
        }))
    
    def update_vehicle(self, camera_id, vehicle_data, current_time, is_inside_polygon):
        """Avtomobil ma'lumotlarini yangilash"""
        track_id = vehicle_data['track_id']
        
        # Ensure track_id is hashable
        if isinstance(track_id, dict):
            if 'id' in track_id:
                track_id = track_id['id']
            else:
                print(f"Error: track_id is a dict without 'id' key: {track_id}")
                return
        if not isinstance(track_id, (int, str)):
            print(f"Error: track_id is not hashable: {track_id} (type: {type(track_id)})")
            return
        
        # Asosiy ma'lumotlarni saqlash
        vehicle_info = self.vehicle_tracking[camera_id][track_id]
        vehicle_info['class_id'] = vehicle_data['class_id']
        vehicle_info['class_name'] = vehicle_data['class_name']
        vehicle_info['bbox'] = vehicle_data['bbox']
        vehicle_info['center'] = vehicle_data['center']
        vehicle_info['confidence'] = vehicle_data['confidence']
        vehicle_info['last_seen'] = current_time
        
        # Polygon holati o'zgarishini kuzatish
        if is_inside_polygon:
            if not vehicle_info['in_polygon']:
                # Polygon ichiga kirdi
                vehicle_info['start_time'] = current_time
                vehicle_info['in_polygon'] = True
                print(f"Kamera {camera_id}: Avtomobil {track_id} polygon ichiga kirdi")
        else:
            if vehicle_info['in_polygon']:
                # Polygondan chiqdi
                vehicle_info['end_time'] = current_time
                vehicle_info['in_polygon'] = False
                vehicle_info['total_time'] = vehicle_info['end_time'] - vehicle_info['start_time']
                print(f"Kamera {camera_id}: Avtomobil {track_id} polygondan chiqdi. Vaqt: {vehicle_info['total_time']:.1f}s")
    
    def get_vehicle_info(self, camera_id, track_id):
        """Avtomobil ma'lumotlarini olish"""
        return self.vehicle_tracking[camera_id][track_id]
    
    def get_all_vehicles(self, camera_id):
        """Kameradagi barcha avtomobillar ma'lumotlarini olish"""
        return self.vehicle_tracking[camera_id]
    
    def cleanup_old_vehicles(self, camera_id, current_time, timeout=30):
        """Uzoq vaqt ko'rinmagan avtomobillarni tozalash"""
        to_remove = []
        for track_id, vehicle_info in self.vehicle_tracking[camera_id].items():
            if current_time - vehicle_info['last_seen'] > timeout:
                to_remove.append(track_id)
        
        for track_id in to_remove:
            del self.vehicle_tracking[camera_id][track_id]
            print(f"Kamera {camera_id}: Avtomobil {track_id} kesh dan o'chirildi")
    
    def draw_vehicle_info(self, frame, camera_id, track_id, speed_info=None):
        """Avtomobil ma'lumotlarini framega chizish"""
        vehicle_info = self.vehicle_tracking[camera_id][track_id]
        
        if vehicle_info['bbox'] is None:
            return frame
        
        x1, y1, x2, y2 = vehicle_info['bbox']
        
        # Matn rangini tanlash
        if vehicle_info['in_polygon']:
            text_color = TEXT_SETTINGS['colors']['inside_polygon']
        else:
            text_color = TEXT_SETTINGS['colors']['outside_polygon']
        
        # Asosiy ma'lumotlar
        y_offset = 0
        
        # ID va klass
        info_text = f"ID:{track_id} {vehicle_info['class_name']}"
        cv2.putText(frame, info_text, (x1, y1-20+y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
        y_offset += 15
        
        # Tezlik ma'lumotlari (agar mavjud bo'lsa)
        if speed_info and speed_info.get('current_speed', 0) > 0:
            if vehicle_info['in_polygon']:
                time_text = f"Vaqt: {speed_info['time_in_polygon']:.1f}s"
                speed_text = f"Tezlik: {speed_info['current_speed']:.1f}km/h"
            else:
                time_text = f"Jami: {vehicle_info['total_time']:.1f}s"
                speed_text = f"O'rtacha: {speed_info['average_speed']:.1f}km/h"
            
            cv2.putText(frame, time_text, (x1, y1-20+y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
            y_offset += 15
            
            cv2.putText(frame, speed_text, (x1, y1-20+y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
        
        return frame
    
    def get_statistics(self, camera_id):
        """Kamera statistikalarini olish"""
        vehicles = self.vehicle_tracking[camera_id]
        
        stats = {
            'total_vehicles': len(vehicles),
            'active_in_polygon': sum(1 for v in vehicles.values() if v['in_polygon']),
            'completed_vehicles': sum(1 for v in vehicles.values() if v['total_time'] > 0),
            'vehicles_data': []
        }
        
        for track_id, vehicle_info in vehicles.items():
            if vehicle_info['total_time'] > 0:
                stats['vehicles_data'].append({
                    'id': track_id,
                    'class': vehicle_info['class_name'],
                    'time': vehicle_info['total_time'],
                    'speed': vehicle_info['speed']
                })
        
        return stats