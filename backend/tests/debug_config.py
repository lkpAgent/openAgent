import sys
import os
from pathlib import Path
import yaml
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from open_agent.core.config import Settings

def debug_config_loading():
    print("Debug configuration loading...")
    
    # 直接读取YAML文件
    config_path = Path(__file__).parent / "configs" / "settings.yaml"
    print(f"Config file path: {config_path}")
    print(f"Config file exists: {config_path.exists()}")
    
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)
        
        print("\nRaw YAML config:")
        print(f"Vector DB section: {raw_config.get('vector_db', 'NOT FOUND')}")
        
        # 测试展平逻辑
        flat_config = Settings._flatten_config(raw_config)
        print("\nFlattened config (vector_db related):")
        for key, value in flat_config.items():
            if 'vector' in key.lower():
                print(f"  {key}: {value}")
        
        # 测试Settings加载
        settings = Settings.load_from_yaml(str(config_path))
        print(f"\nLoaded Settings:")
        print(f"  Vector DB type: {settings.vector_db.type}")
        print(f"  PGVector host: {settings.vector_db.pgvector_host}")
        
    else:
        print("Config file not found!")

if __name__ == "__main__":
    debug_config_loading()