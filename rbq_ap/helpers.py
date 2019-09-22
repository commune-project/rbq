def get_id(data):
    if isinstance(data, dict):
        if "id" in data.keys():
            return data["id"]
    return data