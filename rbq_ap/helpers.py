from typing import Union, Dict, Optional
def get_id(data: Union[str, Dict[str, str]]) -> Optional[str]:
    """
    Get object id.

    The object id of a str is itself
    """
    if isinstance(data, dict):
        if "id" in data.keys():
            return data["id"]
    if isinstance(data, str):
        return data
    else:
        return None