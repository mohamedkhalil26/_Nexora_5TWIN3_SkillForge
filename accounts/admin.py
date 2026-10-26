"""Admin accounts — Ch3 : ModelAdmin personnalise + groupes + actions en masse."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import NIVEAUX, ROLES, Utilisateur


@admin.action(description="Promouvoir en mentor")
def promouvoir_mentor(modeladmin, request, queryset):
    queryset.update(role="mentor")


@admin.action(description="Repasser en apprenant")
def repasser_apprenant(modeladmin, request, queryset):
    queryset.update(role="apprenant")


@admin.action(description="Promouvoir en admin (avec acces staff)")
def promouvoir_admin(modeladmin, request, queryset):
    queryset.update(role="admin", is_staff=True)


@admin.action(description="Désactiver les comptes")
def desactiver_comptes(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ("username", "email", "role", "niveau", "is_staff", "is_active")
    list_filter = ("role", "niveau", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
    actions = [promouvoir_mentor, promouvoir_admin, repasser_apprenant, desactiver_comptes]
    fieldsets = UserAdmin.fieldsets + (
        (
            "Profil SkillForge",
            {"fields": ("role", "telephone", "niveau", "objectifs", "bio", "avatar")},
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Profil SkillForge",
            {"fields": ("email", "role", "telephone", "niveau", "objectifs")},
        ),
    )

    def has_delete_permission(self, request, obj=None):
        # Ch3 : on ne supprime jamais un superuser depuis l'admin.
        if obj is not None and obj.is_superuser:
            return False
        return super().has_delete_permission(request, obj)
