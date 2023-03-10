from services.authentication_service import TokenService
from cores.databases.connection import get_db
from db import User
from cores.schemas.sche_base import DataResponse
import random
from sqlalchemy import func, or_

class UserService():
    def __init__(self, user_token: str, uid: int =None):
        # - user_token: id of the user that want to perform the action. It will also authorized the user to perform 
        # other actions: change avatar, change cover photo
        # - uid : id of the user that will be interacted with. Eg: get their info, get their posts, etc...
        self.user_token = user_token
        self.uid = uid
        self.is_owner = False
        self.session = next(get_db())
        if self.uid:
            self.__verify_owner()
        
    def __verify_owner(self):
        token_service = TokenService(token=self.user_token)
        uid = token_service.get_uid_from_token()
        if uid == self.uid:
            self.is_owner = True
            
    def get_my_profile(self):
        token_service = TokenService(token=self.user_token)
        uid = token_service.get_uid_from_token()
        user = self.session.query(User).filter(User.id == uid, User.is_verified == True, User.deleted_at == None).first()
        if not user:
            return DataResponse().custom_response(500, False, "User not found")
        data =  user.__repr__()
        return DataResponse().success_response(data)

    def get_profile(self):
        user = self.session.query(User).filter(User.id == self.uid, User.is_verified == True, User.deleted_at == None).first()
        if not user:
            return DataResponse().custom_response(500, False, "User not found")
        
        data =  user.__repr__()
        data['is_owner'] = self.is_owner
        return DataResponse().success_response(data)

    def update_profile(self, info):
        if self.is_owner == False:
            return DataResponse().custom_response(405, False, "What à dú đo ình")
        
        info = {key: value for key, value in info.dict().items() if value is not None}

        if 'username' in info:
            duplicate_user_username = self.session.query(User).filter(User.username == info['username']).first()
            if duplicate_user_username:
                return DataResponse().custom_response(500, False, f"Username already exists")

        user = self.session.query(User).filter(User.id == self.uid, User.is_verified == True, User.deleted_at == None).first()
        if not user:
            return DataResponse().custom_response(500, False, "User not found")
        try:
            key_column_map = {
                'username': User.username,
                'full_name': User.full_name,
                'phone': User.phone,
                'bio': User.bio,
                'dob': User.dob,
                'gender': User.gender,
                'location': User.location,
            }
            
            for key, value in info.items():
                column = key_column_map.get(key)
                if column is not None:
                    setattr(user, column.name, value)
            user.update_time()
            self.session.commit()
            return DataResponse().custom_response(200, True, info)
        except Exception:
            return DataResponse().custom_response(501, False, 'Something went wrong. Please try again later.')
        
    def update_avatar(self, **kwargs):
        if self.is_owner == False:
            return DataResponse().custom_response(405, False, "What à dú đo ình")
        user = self.session.query(User).filter(User.id == self.uid, User.is_verified == True, User.deleted_at == None).first()
        if not user:
            return DataResponse().custom_response(500, False, "User not found")
        try:
            if 'avatar' in kwargs:
                user.avatar = kwargs['avatar']
            if 'avatar_2nd' in kwargs:
                user.avatar_2nd = kwargs['avatar_2nd']
            user.update_time()
            self.session.commit()
            
            return DataResponse().custom_response(200, True, 'Update succeed')
        except Exception as e:
            return DataResponse().custom_response(501, False, 'Something went wrong. Please try again later.')
        
    def get_profile_posts(self):
        user = self.session.query(User).filter(User.id == self.uid, User.is_verified == True, User.deleted_at == None).first()
        if not user:
            return DataResponse().custom_response(500, False, "User not found")
        posts = user.posts
        posts = [ item.__repr__() for item in posts if item.deleted_at == None]
        posts = sorted(posts, key=lambda x: x['id'], reverse=True)
        return DataResponse().success_response(posts)
    
    def suggest_friends(self, batch):
        num_rows = self.session.query(User).count()
        if batch > num_rows:
            batch = num_rows
        token_service = TokenService(token=self.user_token)
        uid = token_service.get_uid_from_token()
        query = self.session.query(User).filter(
            User.id != uid, 
            User.is_verified == True, 
            User.deleted_at == None, 
        ).order_by(func.rand()).limit(batch)
        users = query.all()

        users = [item.__repr__() for item in users]
        return DataResponse().success_response(users)

    def search_users(self, kw):
        token_service = TokenService(token=self.user_token)
        user_id = token_service.get_uid_from_token()

        users = self.session.query(User).filter(
            or_(
                func.lower(User.username).contains(func.lower(kw)),
                func.lower(User.full_name).contains(func.lower(kw)),
            ),
            User.id != user_id
        ).limit(5).all()
        users = [item.__repr__() for item in users]
        return DataResponse().success_response(users)