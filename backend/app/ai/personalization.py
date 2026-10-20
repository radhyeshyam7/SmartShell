import uuid
from typing import List, Dict, Optional
from datetime import datetime
from backend.app.database.database import get_db
from backend.app.database.models import UserPreferenceModel

class PersonalizationManager:
    """Manages user-approved explicit preferences and personalization rules"""

    def save_preference(self, category: str, user_key: str, preference_value: str) -> Dict:
        """Store explicit user preference rule"""
        try:
            db = next(get_db())
            # Check if key already exists, update if so
            existing = db.query(UserPreferenceModel).filter(
                UserPreferenceModel.user_key == user_key.lower().strip()
            ).first()
            
            if existing:
                existing.preference_value = preference_value
                existing.category = category
                existing.is_active = True
                db.commit()
                return {"id": existing.id, "status": "updated", "key": user_key, "value": preference_value}
            
            pref_id = f"pref-{uuid.uuid4().hex[:8]}"
            record = UserPreferenceModel(
                id=pref_id,
                category=category,
                user_key=user_key.lower().strip(),
                preference_value=preference_value,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(record)
            db.commit()
            return {"id": pref_id, "status": "created", "key": user_key, "value": preference_value}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_applicable_preferences(self, prompt: str) -> List[Dict]:
        """Retrieve preferences applicable to the prompt context"""
        try:
            db = next(get_db())
            active_prefs = db.query(UserPreferenceModel).filter(UserPreferenceModel.is_active == True).all()
            matched = []
            prompt_lower = prompt.lower()
            for pref in active_prefs:
                if pref.user_key in prompt_lower or pref.category in prompt_lower:
                    matched.append({
                        "category": pref.category,
                        "key": pref.user_key,
                        "value": pref.preference_value
                    })
            return matched
        except Exception:
            return []

    def list_preferences(self) -> List[Dict]:
        """List all active saved preferences"""
        try:
            db = next(get_db())
            prefs = db.query(UserPreferenceModel).filter(UserPreferenceModel.is_active == True).all()
            return [{
                "id": p.id,
                "category": p.category,
                "user_key": p.user_key,
                "preference_value": p.preference_value,
                "created_at": str(p.created_at)
            } for p in prefs]
        except Exception:
            return []

    def delete_preference(self, pref_id: str) -> bool:
        """Deactivate/delete a saved user preference"""
        try:
            db = next(get_db())
            pref = db.query(UserPreferenceModel).filter(UserPreferenceModel.id == pref_id).first()
            if pref:
                pref.is_active = False
                db.commit()
                return True
            return False
        except Exception:
            return False

personalization_manager = PersonalizationManager()
