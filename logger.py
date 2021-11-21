def custom(text, emoji=""):
    print(f"{emoji} | {text}")

def log(text):
    custom(text, "ℹ️")

def success(text):
    custom(text, "✅")
    
def error(text):
    custom(text, "❌")