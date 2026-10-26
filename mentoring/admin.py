"""Admin mentoring — Ch3 : disponibilites inline + actions confirmer/terminer."""
from django.contrib import admin
from django.utils import timezone

from .models import Disponibilite, MentorProfile, Message, Reservation


@admin.action(description="Confirmer les réservations")
def confirmer_reservations(modeladmin, request, queryset):
    for resa in queryset.filter(statut="en_attente"):
        resa.statut = "confirmee"
        resa.generer_lien_visio()
        resa.save(update_fields=["statut", "lien_visio"])


@admin.action(description="Marquer comme terminées")
def terminer_reservations(modeladmin, request, queryset):
    queryset.filter(statut="confirmee").update(statut="terminee")


@admin.action(description="Vérifier les mentors")
def verifier_mentors(modeladmin, request, queryset):
    queryset.update(verifie=True)


class DisponibiliteInline(admin.TabularInline):
    model = Disponibilite
    extra = 0
    fields = ("debut", "fin", "reserve")


@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
    list_display = ("mentor", "tarif", "verifie", "nb_dispos")
    list_filter = ("verifie", "specialites")
    search_fields = ("mentor__username", "presentation")
    filter_horizontal = ("specialites",)
    actions = [verifier_mentors]
    inlines = [DisponibiliteInline]

    @admin.display(description="Créneaux")
    def nb_dispos(self, obj):
        return obj.disponibilites.count()


@admin.register(Disponibilite)
class DisponibiliteAdmin(admin.ModelAdmin):
    list_display = ("__str__", "mentor", "debut", "fin", "reserve")
    list_filter = ("reserve", "mentor", "debut")
    ordering = ("debut",)


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("auteur", "contenu", "date")
    can_delete = False


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("__str__", "statut", "cree_le")
    list_filter = ("statut", "cree_le")
    search_fields = ("apprenant__username", "sujet")
    ordering = ("-cree_le",)
    actions = [confirmer_reservations, terminer_reservations]
    inlines = [MessageInline]
    readonly_fields = ("lien_visio",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("__str__", "reservation", "auteur", "date", "lu")
    list_filter = ("lu", "date")
    search_fields = ("contenu", "auteur__username")
