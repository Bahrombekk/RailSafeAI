"""
RailSafeAI - Fayl yo'llari konfiguratsiyasi
"""
import os
from config.settings import SAVE_SETTINGS

class Paths:
    """Fayl va papka yo'llarini boshqarish"""
    
    # Asosiy papkalar
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CONFIG_DIR = os.path.join(ROOT_DIR, 'config')
    DATA_DIR = os.path.join(ROOT_DIR, 'data')
    MODELS_DIR = os.path.join(ROOT_DIR, 'models')
    MODULES_DIR = os.path.join(ROOT_DIR, 'modules')
    
    # Ma'lumotlar papkalari
    VIDEOS_DIR = os.path.join(DATA_DIR, 'videos')
    POLYGONS_DIR = os.path.join(DATA_DIR, 'polygons')
    OUTPUTS_DIR = os.path.join(DATA_DIR, SAVE_SETTINGS['output_dir'].split('/')[-1])
    
    # Chiquvchi fayllar
    VEHICLE_VIDEOS_DIR = os.path.join(OUTPUTS_DIR, SAVE_SETTINGS['video_dir'])
    VEHICLE_IMAGES_DIR = os.path.join(OUTPUTS_DIR, SAVE_SETTINGS['image_dir'])
    
    @staticmethod
    def create_directories():
        """Zaruriy papkalarni yaratish"""
        directories = [
            Paths.DATA_DIR,
            Paths.VIDEOS_DIR,
            Paths.POLYGONS_DIR, 
            Paths.OUTPUTS_DIR,
            Paths.VEHICLE_VIDEOS_DIR,
            Paths.VEHICLE_IMAGES_DIR
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Papka yaratildi: {directory}")
    
    @staticmethod
    def get_polygon_path(polygon_file):
        """Polygon fayl yo'lini olish"""
        if os.path.isabs(polygon_file):
            return polygon_file
        return os.path.join(Paths.POLYGONS_DIR, polygon_file)
    
    @staticmethod
    def get_model_path(model_file):
        """Model fayl yo'lini olish"""
        if os.path.isabs(model_file):
            return model_file
        return os.path.join(Paths.MODELS_DIR, model_file)
    
    @staticmethod
    def get_video_save_path(filename):
        """Video saqlash yo'lini olish"""
        return os.path.join(Paths.VEHICLE_VIDEOS_DIR, filename)
    
    @staticmethod
    def get_image_save_path(filename):
        """Rasm saqlash yo'lini olish"""
        return os.path.join(Paths.VEHICLE_IMAGES_DIR, filename)