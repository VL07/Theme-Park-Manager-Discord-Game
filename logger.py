def custom(text, emoji=""):
    print(f"{emoji} | {text}")

def log(text):
    custom(text, "âšī¸")

def success(text):
    custom(text, "â")
    
def error(text):
    custom(text, "â")