from django.urls import path, include
from . import views

# urlpatterns = [
#     path('login/', views.login, name='login'),
#     path('logout/', views.logout, name='logout'),
#     path('register/', views.register, name="register"),
#     path('verify-account/', views.verify_account, name="verify_account"),
#     path('forgot-password/', views.send_password_reset_link, name="reset_password_via_email"),
#     path('verify-password-reset-link/', views.verify_password_reset_link, name="verify_password_reset_link"),
#     path('set-new-password/', views.set_new_password_using_reset_link, name="set_new_password")
# ]

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    #path('forgot-password/', views.send_password_reset_link, name="reset_password_via_email"),
    path('logout/', views.logout, name='logout'),
    path('verify-password-reset-link/', views.verify_password_reset_link, name="verify_password_reset_link"),
    path('verify_account/<uuid:user_id>/', views.verify_account, name='verify_account'),
    path('set-new-password/', views.set_new_password_using_reset_link, name="set_new_password"),
    path('reset-password-via-email/', views.reset_password_via_email, name='reset_password_via_email'),
    path('reset-password/<uidb64>/<token>/', views.reset_password_confirm, name='reset_password_confirm'),
]
