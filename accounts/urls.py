from django.urls import path
from . import views

urlpatterns = [
    #path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('register/', views.register, name="register"),
    path('verify-account/', views.verify_account, name="verify_account"),
    path('forgot-password/', views.send_password_reset_link, name="reset_password_via_email"),
    path('verify-password-reset-link', views.verify_password_reset_link, name="verify_password_reset_link"),
    path('set-new-password', views.set_new_password_using_reset_link, name="set_new_password"),

    # Candidate & Company
    path("candidate/login/", views.candidate_login, name="candidate_login"),
    path("company/login/", views.company_login, name="company_login"),
    path('company/home/', views.company_home, name='company_home'),
    path('candidate/home/', views.candidate_home, name='candidate_home'),

    # Admin dashboard
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/companies/", views.admin_companies, name="admin_companies"),
    path("admin/candidates/", views.admin_candidates, name="admin_candidates"),
    path("admin/add-question/", views.admin_add_question, name="admin_add_question"),

    # ✅ Question Management
    path("admin/questions/", views.admin_questions, name="admin_questions"),
    path("admin/questions/edit/<int:question_id>/", views.edit_question, name="edit_question"),
    path("admin/questions/delete/<int:question_id>/", views.delete_question, name="delete_question"),

    # Admin login modal
    path('admin-login-modal/', views.admin_login_modal, name='admin_login_modal'),
]
