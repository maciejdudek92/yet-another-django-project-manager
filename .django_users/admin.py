# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import User


class UserAdmin(BaseUserAdmin):
    # add_form_template = "admin/auth/user/add_form.html"
    # change_user_password_template = None
    # fieldsets = (
    #     (None, {"fields": ("email", "password")}),
    #     (_("Personal info"), {"fields": ("first_name", "last_name", "phone_number")}),
    #     (
    #         _("Permissions"),
    #         {
    #             "fields": (
    #                 "is_active",
    #                 "is_staff",
    #                 "is_superuser",
    #                 "groups",
    #                 "user_permissions",
    #             ),
    #         },
    #     ),
    #     (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    # )
    # add_fieldsets = (
    #     (
    #         None,
    #         {
    #             "classes": ("wide",),
    #             "fields": ("email", "password1", "password2"),
    #         },
    #     ),
    # )
    # form = UserAdminChangeForm
    # add_form = UserAdminCreationForm
    # change_password_form = AdminPasswordChangeForm
    # list_display = ("email", "first_name", "last_name", "is_staff")
    # list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    # search_fields = ("email", "first_name", "last_name")
    # ordering = ("email",)
    # filter_horizontal = (
    #     "groups",
    #     "user_permissions",
    # )

    # The forms to add and change user instances
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = [
        "email",
    ]

    list_filter = [
        "email",
    ]
    fieldsets = (
        (None, {"fields": ("email", "first_name", "last_name", "password", "user_type", "image")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_staff",
                    "is_superuser",
                    "is_active",
                ),
            },
        ),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "first_name", "last_name", "password1", "password2", "image")}),
        # (
        #     "Permissions",
        #     {"fields": ("is_admin", "is_staff", "is_active", )},
        # ),
    )
    search_fields = ["email"]
    ordering = ["email"]
    filter_horizontal = ()


admin.site.register(User, UserAdmin)
