"""
RailSafeAI - Tezlik hisoblash moduli
"""
from config.settings import SPEED_ESTIMATION_ENABLED

class SpeedEstimator:
    """Avtomobil tezligini hisoblash uchun klass"""
    
    def __init__(self):
        self.enabled = SPEED_ESTIMATION_ENABLED
        
    def calculate_speed(self, distance_meters, time_seconds):
        """Tezlikni km/h da hisoblash"""
        if not self.enabled:
            return 0
        
        if time_seconds == 0:
            return 0
            
        speed_mps = distance_meters / time_seconds  # Metr/sekund
        speed_kmh = speed_mps * 3.6  # km/soat ga o'tkazish
        return speed_kmh
    
    def calculate_current_speed(self, distance_meters, current_time, start_time):
        """Joriy tezlikni hisoblash (hali polygon ichida bo'lgan vaqt)"""
        if not self.enabled:
            return 0
        
        time_diff = current_time - start_time
        if time_diff > 0:
            return self.calculate_speed(distance_meters, time_diff)
        return 0
    
    def is_enabled(self):
        """Tezlik hisoblash yoqilganligini tekshirish"""
        return self.enabled
    
    def set_enabled(self, enabled):
        """Tezlik hisoblashni yoqish/o'chirish"""
        self.enabled = enabled
        print(f"Tezlik hisoblash: {'YOQILDI' if enabled else "O'CHIRILDI"}")
    
    def get_speed_info(self, vehicle_data, current_time, polygon_length):
        """Avtomobil uchun tezlik ma'lumotlarini olish"""
        if not self.enabled:
            return {
                'current_speed': 0,
                'average_speed': 0,
                'time_in_polygon': 0
            }
        
        info = {
            'current_speed': 0,
            'average_speed': 0,
            'time_in_polygon': 0
        }
        
        if vehicle_data['in_polygon'] and vehicle_data['start_time'] is not None:
            # Hozirgi tezlik (polygon ichida bo'lgan vaqt davomida)
            time_in_polygon = current_time - vehicle_data['start_time']
            info['time_in_polygon'] = time_in_polygon
            info['current_speed'] = self.calculate_current_speed(
                polygon_length, current_time, vehicle_data['start_time']
            )
        
        if vehicle_data['total_time'] > 0:
            # O'rtacha tezlik (polygondan butunlay o'tgan vaqt)
            info['average_speed'] = self.calculate_speed(
                polygon_length, vehicle_data['total_time']
            )
        
        return info