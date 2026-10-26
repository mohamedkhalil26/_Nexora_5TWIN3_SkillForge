"""Admin certification — Ch3 : certificats readonly + regeneration PDF."""
from django.contrib import admin
from django.core.files.base import ContentFile

from .models import Certificat
from .pdf import generer_certificat_pdf


@admin.action(description="Régénérer le PDF")
def regenerer_pdf(modeladmin, request, queryset):
    for cert in queryset:
        pdf = generer_certificat_pdf(cert)
        cert.fichier.save(f"certificat-{cert.code}.pdf", ContentFile(pdf), save=True)


@admin.register(Certificat)
class CertificatAdmin(admin.ModelAdmin):
    list_display = ("__str__", "apprenant", "competence", "score_final", "delivre_le")
    list_filter = ("competence", "delivre_le")
    search_fields = ("apprenant__username", "competence__nom", "code")
    ordering = ("-delivre_le",)
    readonly_fields = ("code", "score_final", "fichier", "delivre_le")
    actions = [regenerer_pdf]

    def has_add_permission(self, request):
        # Les certificats naissent depuis l'app (eligibilite), pas depuis l'admin.
        return False
