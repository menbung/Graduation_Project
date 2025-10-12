from PIL import Image

def image_to_embedding(image_path: str):
    img = Image.open(image_path).convert('RGB')
    return [0.0] * 512
