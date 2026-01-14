import os
file_path = "/Users/Cyrpien/Desktop/Cours Master 2/Google Project/Clarity_MVP/temp/test_image.jpg"
abs_path = os.path.abspath(file_path)
print(f"Chemin absolu : {abs_path}")
print(f"Fichier existe : {os.path.exists(abs_path)}")
print(f"Permissions : {oct(os.stat(abs_path).st_mode)[-3:]}")
with open(abs_path, 'rb') as f:
    print(f"Taille du fichier : {len(f.read())} octets")



