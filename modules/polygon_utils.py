"""
RailSafeAI - Polygon bilan ishlash moduli
"""
import json
import numpy as np
import cv2
from config.paths import Paths
from config.settings import POLYGON_SETTINGS

class PolygonManager:
    """Polygon bilan ishlash uchun klass"""
    
    def __init__(self):
        self.polygons = {}  # Har bir kamera uchun polygon
    
    def load_polygon(self, camera_id, polygon_file):
        """JSON fayldan polygon ma'lumotlarini yuklash"""
        try:
            polygon_path = Paths.get_polygon_path(polygon_file)
            with open(polygon_path, 'r') as f:
                polygon_data = json.load(f)
            
            # Polygon koordinatalarini chiqarish
            if 'annotations' in polygon_data and len(polygon_data['annotations']) > 0:
                segmentation = polygon_data['annotations'][0]['segmentation'][0]
                polygon_points = np.array(segmentation).reshape(-1, 2)
                self.polygons[camera_id] = polygon_points
                print(f"Kamera {camera_id} uchun polygon yuklandi: {len(polygon_points)} nuqta")
                return True
            else:
                print(f"Xato: {polygon_path} faylida annotations topilmadi")
                return False
                
        except FileNotFoundError:
            print(f"Xato: {polygon_path} fayli topilmadi")
            return False
        except json.JSONDecodeError:
            print(f"Xato: {polygon_path} fayli noto'g'ri JSON format")
            return False
        except Exception as e:
            print(f"Xato polygon yuklashda: {e}")
            return False
    
    def point_in_polygon(self, camera_id, point):
        """Nuqtaning polygon ichida ekanligini tekshirish"""
        if camera_id not in self.polygons:
            return False
        
        polygon = self.polygons[camera_id]
        return self._point_in_polygon_algorithm(point, polygon)
    
    def _point_in_polygon_algorithm(self, point, polygon):
        """Ray-casting algoritmi yordamida nuqtaning polygon ichida ekanligini aniqlash"""
        x, y = point
        n = len(polygon)
        inside = False
        p1x, p1y = polygon[0]
        
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside
    
    def draw_polygon(self, frame, camera_id):
        """Framega polygon chizish"""
        if camera_id not in self.polygons:
            return frame
        
        polygon = self.polygons[camera_id]
        
        # Polygon chizgisini chizish
        cv2.polylines(
            frame, 
            [polygon.astype(np.int32)], 
            True, 
            POLYGON_SETTINGS['line_color'], 
            POLYGON_SETTINGS['line_thickness']
        )
        
        # Agar kerak bo'lsa, polygon ichini to'ldirish
        if POLYGON_SETTINGS.get('fill_alpha', 0) > 0:
            overlay = frame.copy()
            cv2.fillPoly(
                overlay, 
                [polygon.astype(np.int32)], 
                POLYGON_SETTINGS['line_color']
            )
            cv2.addWeighted(
                overlay, 
                POLYGON_SETTINGS['fill_alpha'], 
                frame, 
                1 - POLYGON_SETTINGS['fill_alpha'], 
                0, 
                frame
            )
        
        return frame
    
    def get_polygon_bounds(self, camera_id):
        """Polygon chegaralarini olish"""
        if camera_id not in self.polygons:
            return None
        
        polygon = self.polygons[camera_id]
        min_x = int(np.min(polygon[:, 0]))
        max_x = int(np.max(polygon[:, 0]))
        min_y = int(np.min(polygon[:, 1]))
        max_y = int(np.max(polygon[:, 1]))
        
        return (min_x, min_y, max_x, max_y)