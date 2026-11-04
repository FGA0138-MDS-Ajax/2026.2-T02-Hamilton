from django.contrib.auth import get_user_model;

from .models import Profile;

class AccountService:
    @staticmethod
    def create_account(user):
        # cria um perfil automaticamente para
        # o usuário criado.
        Profile.objects.create(
            user=user
        );

        return user;
