
import os
import sys
# Path hack
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../"))
sys.path.append(project_root)

from core.services.image_renderer.unidades_renderer import UnidadesRenderer

def main():
    print("Initializing Renderer...")
    renderer = UnidadesRenderer()
    
    mock_data = {
        "date": "2025-12-22",
        "new": [{"codigo": f"237{i}", "nome": "Test", "valor": 100} for i in range(1)],
        "cancelled": [],
        "upsell": []
    }
    
    print("Generating...")
    try:
        output = renderer.generate_unidades_reports(mock_data, output_path="debug_out.pdf")
        print(f"Success: {output}")
    except Exception as e:
        print("CRITICAL ERROR CAUGHT:")
        print(e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
