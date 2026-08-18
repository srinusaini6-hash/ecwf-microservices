from sqlalchemy.orm import Session

from app.models import UserAccountSetting, UserProfile


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def profile(self, user_id: int):
        return self.db.get(UserProfile, user_id)

    def settings(self, user_id: int):
        return self.db.get(UserAccountSetting, user_id)

    def ensure(self, user_id: int):
        profile = self.profile(user_id)
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
        settings_obj = self.settings(user_id)
        if not settings_obj:
            settings_obj = UserAccountSetting(user_id=user_id)
            self.db.add(settings_obj)
        self.db.commit()
        self.db.refresh(profile)
        self.db.refresh(settings_obj)
        return profile, settings_obj

    def update_profile(self, user_id: int, values: dict):
        profile, _ = self.ensure(user_id)
        for key, value in values.items():
            if value is not None:
                setattr(profile, key, value)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def update_settings(self, user_id: int, values: dict):
        _, settings_obj = self.ensure(user_id)
        for key, value in values.items():
            if value is not None:
                setattr(settings_obj, key, value)
        self.db.commit()
        self.db.refresh(settings_obj)
        return settings_obj
