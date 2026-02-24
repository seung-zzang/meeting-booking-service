from sqladmin import ModelView
from appserver.apps.account.models import User


class UserAdmin(ModelView, model=User):
    pass