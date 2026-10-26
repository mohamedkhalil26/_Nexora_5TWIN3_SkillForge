"""Generation du PDF de certificat (reportlab) — offline, sans API externe."""
import io

from django.conf import settings


def generer_certificat_pdf(certificat) -> bytes:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    w, h = landscape(A4)
    c.setFillColorRGB(0.98, 0.95, 0.90)
    c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setStrokeColorRGB(0.55, 0.42, 0.30)
    c.setLineWidth(4)
    c.rect(30, 30, w - 60, h - 60, fill=0, stroke=1)
    c.setFillColorRGB(0.2, 0.15, 0.1)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(w / 2, h - 120, "SkillForge — Certificat")
    c.setFont("Helvetica", 18)
    c.drawCentredString(
        w / 2, h - 180, f"Décerné à {certificat.apprenant.get_full_name() or certificat.apprenant.username}"
    )
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(w / 2, h - 230, f"Compétence : {certificat.competence.nom}")
    c.setFont("Helvetica", 16)
    c.drawCentredString(w / 2, h - 270, f"Score final : {certificat.score_final:.0f}%")
    c.drawCentredString(w / 2, h - 300, f"Délivré le {certificat.delivre_le:%d/%m/%Y}")
    c.setFont("Helvetica-Oblique", 11)
    c.drawCentredString(w / 2, 70, f"Code de vérification : {certificat.code}")
    c.drawCentredString(w / 2, 52, "Learn. Practice. Connect. Get Certified.")
    c.showPage()
    c.save()
    return buf.getvalue()
