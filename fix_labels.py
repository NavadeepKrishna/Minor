import os
import glob

# --- CONFIGURATION ---
# This points to the root of your dataset
# (the folder that contains 'train', 'valid', and 'test')
DATA_ROOT_DIR = './custom_data'
TARGET_CLASS_ID = '0'
# ---------------------

print("Starting label file correction...")
print(f"Targeting root directory: {DATA_ROOT_DIR}")

total_files_checked = 0
total_lines_changed = 0

# Loop through train, valid, and test folders
for sub_dir in ['train', 'valid', 'test']:
    labels_dir = os.path.join(DATA_ROOT_DIR, sub_dir, 'labels')
    
    if not os.path.exists(labels_dir):
        print(f"Skipping: Directory not found {labels_dir}")
        continue
    
    print(f"--- Processing {labels_dir} ---")
    
    # Find all .txt files in the directory
    label_files = glob.glob(os.path.join(labels_dir, '*.txt'))
    
    for label_path in label_files:
        total_files_checked += 1
        new_content = []
        changed = False
        
        try:
            with open(label_path, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                parts = line.strip().split()
                if not parts:
                    continue # skip empty lines
                
                original_class_id = parts[0]
                
                # If the class ID is not '0', change it
                if original_class_id != TARGET_CLASS_ID:
                    changed = True
                    total_lines_changed += 1
                    parts[0] = TARGET_CLASS_ID # Set the class to '0'
                
                new_content.append(" ".join(parts) + "\n")
            
            # Re-write the file with the corrected content
            if changed:
                with open(label_path, 'w') as f:
                    f.writelines(new_content)
        
        except Exception as e:
            print(f"Error processing {label_path}: {e}")

print("\n--- Correction Complete ---")
print(f"Total files checked: {total_files_checked}")
print(f"Total lines modified: {total_lines_changed}")

if total_lines_changed > 0:
    print("Your label files have been fixed. Please clear the cache and re-run training.")
else:
    print("All label files were already correct.")