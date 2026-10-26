"""Admin learning — Ch3 : inlines + actions publier/depublier."""
from django.contrib import admin

from .models import Competence, Cours, Module, Ressource


@admin.action(description="Publier les cours sélectionnés")
def publier_cours(modeladmin, request, queryset):
    queryset.update(publie=True)


@admin.action(description="Dépublier les cours sélectionnés")
def depublier_cours(modeladmin, request, queryset):
    queryset.update(publie=False)


@admin.register(Competence)
class CompetenceAdmin(admin.ModelAdmin):
    list_display = ("nom", "nb_cours", "slug")
    search_fields = ("nom", "description")
    ordering = ("nom",)
    prepopulated_fields = {"slug": ("nom",)}

    @admin.display(description="Cours")
    def nb_cours(self, obj):
        return obj.cours.count()


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0
    fields = ("titre", "ordre")
    show_change_link = True


@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    list_display = ("titre", "competence", "auteur", "duree_minutes", "publie", "cree_le")
    list_filter = ("publie", "competence", "cree_le")
    search_fields = ("titre", "description", "competence__nom")
    ordering = ("-cree_le",)
    prepopulated_fields = {"slug": ("titre",)}
    list_select_related = ("competence", "auteur")
    actions = [publier_cours, depublier_cours]
    inlines = [ModuleInline]
    fieldsets = (
        ("Contenu", {"fields": ("competence", "titre", "slug", "description")}),
        ("Publication", {"fields": ("auteur", "duree_minutes", "publie")}),
    )


class RessourceInline(admin.TabularInline):
    model = Ressource
    extra = 0


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("titre", "cours", "ordre", "nb_ressources")
    list_filter = ("cours__competence", "cours")
    search_fields = ("titre", "contenu")
    ordering = ("cours", "ordre")
    inlines = [RessourceInline]

    @admin.display(description="Ressources")
    def nb_ressources(self, obj):
        return obj.ressources.count()


@admin.register(Ressource)
class RessourceAdmin(admin.ModelAdmin):
    list_display = ("titre", "module", "type")
    list_filter = ("type", "module__cours")
    search_fields = ("titre", "url")
