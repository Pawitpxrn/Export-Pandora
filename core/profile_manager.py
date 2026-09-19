import json
import os
from typing import Dict, List, Optional, Any

PROFILES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiles")

class ProfileManager:
    """Manages saved mapping profiles so users don't have to reconfigure columns repeatedly."""

    def __init__(self, profiles_dir: str = PROFILES_DIR):
        self.profiles_dir = profiles_dir
        os.makedirs(self.profiles_dir, exist_ok=True)

    def list_profiles(self) -> List[str]:
        """Returns list of profile names available."""
        if not os.path.exists(self.profiles_dir):
            return []
        profiles = []
        for f in os.listdir(self.profiles_dir):
            if f.endswith(".json"):
                # Read internal name or fallback to filename
                path = os.path.join(self.profiles_dir, f)
                try:
                    with open(path, "r", encoding="utf-8") as jf:
                        data = json.load(jf)
                        profiles.append(data.get("profile_name", f[:-5]))
                except Exception:
                    profiles.append(f[:-5])
        return sorted(list(set(profiles)))

    def save_profile(self, profile_name: str, selected_columns: List[str], column_mapping: Dict[str, str]) -> str:
        """Saves a profile to JSON file."""
        # Sanitize Windows invalid filename characters: \ / : * ? " < > |
        invalid_chars = r'\/:*?"<>|'
        safe_filename = "".join(c for c in profile_name if c not in invalid_chars).strip()
        if not safe_filename:
            safe_filename = "default_profile"
        
        file_path = os.path.join(self.profiles_dir, f"{safe_filename}.json")
        data = {
            "profile_name": profile_name.strip(),
            "selected_columns": selected_columns,
            "column_mapping": column_mapping
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return file_path

    def load_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Loads profile data by profile name or filename."""
        if not os.path.exists(self.profiles_dir):
            return None
        
        # 1. Try direct filename match
        for f in os.listdir(self.profiles_dir):
            if f.endswith(".json"):
                path = os.path.join(self.profiles_dir, f)
                try:
                    with open(path, "r", encoding="utf-8") as jf:
                        data = json.load(jf)
                        if data.get("profile_name") == profile_name or f[:-5] == profile_name:
                            return data
                except Exception:
                    continue
        return None

    def delete_profile(self, profile_name: str) -> bool:
        """Deletes a profile JSON file."""
        file_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
