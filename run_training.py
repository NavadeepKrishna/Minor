import os
from ultralytics import YOLO

def main():
    # Load a pre-trained model (e.g., yolov8n.pt)
    model = YOLO('yolov8n.pt') 

    # Train the model using your (now correct) data.yaml file
    print("Starting model training for 10 epochs...")
    results = model.train(data='data.yaml',
                          epochs=30,    # <-- Set to 10 for a fast test
                          imgsz=416)       
    
    print("Training finished.")
    
    # Correctly print the save location
    print(f"Results saved to: {results.save_dir}")
    print(f"Best model weights saved at: {os.path.join(results.save_dir, 'weights', 'best.pt')}")

if __name__ == '__main__':
    main()