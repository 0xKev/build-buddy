# ========================================
# Image holder to pass to tool context
# ========================================
image_holder = {"b64": None, "mime": None}


def get_latest_image():
    return image_holder.get("b64"), image_holder.get("mime")
